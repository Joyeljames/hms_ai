"""
HMS AI — AI Agent Router
Connects the three agents to the real database with JWT + role security.

Security flow for every endpoint:
  1. JWT verified by get_current_user
  2. Role checked
  3. Data fetched scoped to current_user.clinic_id
  4. Agent runs on that data only
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models import (
    Patient, Visits, Medicine, User,
    Prescription, PrescriptionItem
)
from app.core.auth import get_current_user

from app.agents.doctor_agent import doctor_agent
from app.agents.pharmacy_agent import pharmacy_agent
from app.agents.admin_assistant import (
    ask_admin_assistant,
    set_context,
    clear_conversation
)

router = APIRouter()


# ═════════════════════════════════════════════
# SCHEMAS
# ═════════════════════════════════════════════

class AIGenerateRequest(BaseModel):
    patient_id: str
    symptoms: str


class ApprovedMedicine(BaseModel):
    name: str
    frequency: int
    duration: int
    timing: Optional[str] = "after food"


class AIApproveRequest(BaseModel):
    patient_id: str
    visit_id: Optional[int] = None
    diagnosis: str
    medicines: List[ApprovedMedicine]


class AdminQuestionRequest(BaseModel):
    question: str
    reset: Optional[bool] = False


# ═════════════════════════════════════════════
# DOCTOR AGENT — generate suggestion
# ═════════════════════════════════════════════

@router.post("/doctor/generate")
def ai_generate_prescription(
    request: AIGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Doctor types symptoms -> AI generates a full prescription
    suggestion using the patient's real history and the clinic's
    real inventory. Nothing is saved. Doctor must approve."""

    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can use the AI prescription generator"
        )

    # Patient must belong to this clinic
    patient = db.query(Patient).filter(
        Patient.patient_id == request.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found in this clinic")

    # REAL patient history from database
    visits = db.query(Visits).filter(
        Visits.patient_id == request.patient_id,
        Visits.clinic_id == current_user.clinic_id
    ).order_by(Visits.created_at.desc()).limit(3).all()

    patient_history = [
        {
            "created_at": str(v.created_at.date()) if v.created_at else "N/A",
            "complaint": v.complaint or "N/A",
            "diagnosis": v.diagnosis or "N/A"
        }
        for v in visits
    ]

    # REAL inventory — only in-stock medicines
    medicines = db.query(Medicine).filter(
        Medicine.clinic_id == current_user.clinic_id,
        Medicine.is_active == True,
        Medicine.stock_quantity > 0
    ).all()

    if not medicines:
        raise HTTPException(
            400,
            "No medicines in stock. Add inventory before using the AI generator."
        )

    available_medicines = [
        {"id": m.id, "name": m.name, "stock": m.stock_quantity}
        for m in medicines
    ]

    initial_state = {
        "patient_id": request.patient_id,
        "symptoms": request.symptoms,
        "patient_history": patient_history,
        "available_medicines": available_medicines,
        "diagnosis": "",
        "recommended_medicines": [],
        "interactions": "",
        "doctor_action": "pending_review",
        "final_prescription": {}
    }

    try:
        result = doctor_agent.invoke(initial_state)
    except Exception as e:
        raise HTTPException(500, f"Doctor Agent failed: {str(e)}")

    # Safety filter — drop anything not in real inventory
    real_names = {m.name.lower() for m in medicines}
    ai_medicines = result.get("recommended_medicines", [])

    verified = []
    rejected = []

    for med in ai_medicines:
        if med.get("name", "").lower() in real_names:
            verified.append(med)
        else:
            rejected.append(med.get("name"))

    return {
        "patient_id": request.patient_id,
        "patient_name": patient.name,
        "symptoms": request.symptoms,
        "ai_diagnosis": result.get("diagnosis", ""),
        "ai_medicines": verified,
        "interactions": result.get("interactions", "Not checked"),
        "patient_history_used": len(patient_history),
        "rejected_hallucinations": rejected,
        "requires_approval": True,
        "message": "AI suggestion generated. Doctor approval required before sending to pharmacy."
    }


# ═════════════════════════════════════════════
# DOCTOR AGENT — approve and save
# ═════════════════════════════════════════════

@router.post("/doctor/approve")
def ai_approve_prescription(
    request: AIApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Doctor approves (possibly edited) AI suggestion.
    This is the ONLY place a prescription is actually created."""

    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(403, "Only doctors can approve prescriptions")

    patient = db.query(Patient).filter(
        Patient.patient_id == request.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    if not request.medicines:
        raise HTTPException(400, "Cannot approve an empty prescription")

    new_prescription = Prescription(
        clinic_id=current_user.clinic_id,
        patient_id=request.patient_id,
        doctor_id=current_user.id,
        visit_id=request.visit_id,
        status="pending"
    )
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    items_created = []
    skipped = []

    for med in request.medicines:
        medicine = db.query(Medicine).filter(
            Medicine.name == med.name,
            Medicine.clinic_id == current_user.clinic_id,
            Medicine.is_active == True
        ).first()

        if not medicine:
            skipped.append(med.name)
            continue

        quantity = med.frequency * med.duration

        new_item = PrescriptionItem(
            prescription_id=new_prescription.id,
            medicine_id=medicine.id,
            frequency=med.frequency,
            duration=med.duration,
            quantity=quantity,
            timing=med.timing
        )
        db.add(new_item)
        db.commit()

        items_created.append({
            "medicine_name": medicine.name,
            "frequency": med.frequency,
            "duration": med.duration,
            "quantity": quantity,
            "timing": med.timing
        })

    if not items_created:
        db.delete(new_prescription)
        db.commit()
        raise HTTPException(
            400,
            f"No valid medicines found in inventory: {skipped}"
        )

    return {
        "prescription_id": new_prescription.id,
        "patient_id": request.patient_id,
        "patient_name": patient.name,
        "diagnosis": request.diagnosis,
        "items": items_created,
        "skipped_medicines": skipped,
        "approved_by": current_user.name,
        "status": "sent_to_pharmacy",
        "message": "Prescription approved and sent to pharmacy"
    }


# ═════════════════════════════════════════════
# PHARMACY AGENT
# ═════════════════════════════════════════════

@router.post("/pharmacy/process/{prescription_id}")
def ai_process_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pharmacy Agent checks real stock, flags shortages,
    suggests alternatives, and calculates the bill.
    Nothing is dispensed — pharmacist must confirm."""

    if current_user.role not in ["pharmacist", "admin"]:
        raise HTTPException(403, "Only pharmacists can use this")

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.clinic_id == current_user.clinic_id
    ).first()

    if not prescription:
        raise HTTPException(404, "Prescription not found")

    if prescription.status != "pending":
        raise HTTPException(400, "Prescription already dispensed")

    patient = db.query(Patient).filter(
        Patient.patient_id == prescription.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    # REAL prescription items
    items = db.query(PrescriptionItem).filter(
        PrescriptionItem.prescription_id == prescription_id
    ).all()

    prescription_items = []
    for item in items:
        medicine = db.query(Medicine).filter(
            Medicine.id == item.medicine_id
        ).first()
        prescription_items.append({
            "medicine_id": item.medicine_id,
            "medicine_name": medicine.name if medicine else "Unknown",
            "quantity": item.quantity
        })

    # REAL inventory
    medicines = db.query(Medicine).filter(
        Medicine.clinic_id == current_user.clinic_id,
        Medicine.is_active == True
    ).all()

    inventory = [
        {
            "id": m.id,
            "name": m.name,
            "stock_quantity": m.stock_quantity,
            "price_per_unit": m.price_per_unit
        }
        for m in medicines
    ]

    initial_state = {
        "prescription_id": prescription_id,
        "patient_id": prescription.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "prescription_items": prescription_items,
        "inventory": inventory,
        "stock_check": [],
        "out_of_stock": [],
        "alternatives": [],
        "total_bill": 0.0,
        "pharmacist_action": "pending_review",
        "final_dispense": {}
    }

    try:
        result = pharmacy_agent.invoke(initial_state)
    except Exception as e:
        raise HTTPException(500, f"Pharmacy Agent failed: {str(e)}")

    return {
        "prescription_id": prescription_id,
        "patient_id": prescription.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "stock_check": result.get("stock_check", []),
        "out_of_stock": result.get("out_of_stock", []),
        "ai_alternatives": result.get("alternatives", []),
        "estimated_bill": result.get("total_bill", 0),
        "requires_confirmation": True,
        "message": "Stock verified. Pharmacist confirmation required to dispense."
    }


# ═════════════════════════════════════════════
# ADMIN ASSISTANT
# ═════════════════════════════════════════════

@router.post("/admin/ask")
def ai_admin_ask(
    request: AdminQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ask the clinic's AI business analyst anything.
    The AI decides which tools to call and reasons over the results."""

    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(403, "Only admin can use the AI assistant")

    # Give the tools a DB session scoped to THIS clinic only
    set_context(db, current_user.clinic_id)

    try:
        answer = ask_admin_assistant(
            request.question,
            reset=request.reset,
            verbose=True
        )
    except Exception as e:
        raise HTTPException(500, f"Admin Assistant failed: {str(e)}")

    return {
        "question": request.question,
        "answer": answer,
        "asked_by": current_user.name
    }


@router.post("/admin/clear")
def ai_admin_clear(
    current_user: User = Depends(get_current_user)
):
    """Clear the assistant's conversation memory."""

    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(403, "Only admin can do this")

    clear_conversation()

    return {"message": "Conversation memory cleared"}