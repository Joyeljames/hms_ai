from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Prescription, PrescriptionItem, Patient, Medicine, User
from app.schemas import PrescriptionCreate, PrescriptionResponse
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/create")
def create_prescription(
    prescription:PrescriptionCreate,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user)
):
     # Only doctor or admin
    if current_user.role not in ["doctor","admin"]:
        raise HTTPException(
            status_code=403,
            detail="only doctor and admin can create prescription"
        )

    #check patient exist

    patient = db.query(Patient).filter(
        Patient.patient_id == prescription.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="PATIENT NOT FOUND"
        )

    # CREATE PRESCRIPTION

    new_prescription = Prescription(
        clinic_id  = current_user.clinic_id,
        patient_id = prescription.patient_id,
        doctor_id = current_user.id,
        visit_id = prescription.visit_id,
        status = "pending"
    )
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    # Create prescription items
    item_response = []

    for item in prescription.items:
        # Check medicine exists
        medicine = db.query(Medicine).filter(
            Medicine.id == item.medicine_id,
            Medicine.clinic_id == current_user.clinic_id,
            Medicine.is_active == True
        ).first()

    if not medicine:
            raise HTTPException(
                status_code=404,
                detail=f"Medicine id {item.medicine_id} not found"
            )
        # Auto calculate quantity
    quantity = item.frequency * item.duration

    new_item = PrescriptionItem(
            prescription_id=new_prescription.id,
            medicine_id=item.medicine_id,
            frequency=item.frequency,
            duration=item.duration,
            quantity=quantity,
            timing=item.timing
        )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    item_response.append({
            "id": new_item.id,
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "frequency": new_item.frequency,
            "duration": new_item.duration,
            "quantity": new_item.quantity,
            "timing": new_item.timing
    })

       # Get doctor name
    doctor = db.query(User).filter(
        User.id == current_user.id
    ).first()


    return {
        "id": new_prescription.id,
        "patient_id": new_prescription.patient_id,
        "patient_name": patient.name,
        "doctor_id": new_prescription.doctor_id,
        "doctor_name": doctor.name,
        "visit_id": new_prescription.visit_id,
        "status": new_prescription.status,
        "items": item_response,
        "created_at": new_prescription.created_at
    }

@router.get("/patient/{patient_id}")
def get_patient_prescriptions(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient_id,
        Prescription.clinic_id == current_user.clinic_id
    ).order_by(Prescription.created_at.desc()).all()

    result = []

    for prescription in prescriptions:
        patient = db.query(Patient).filter(
            Patient.patient_id == prescription.patient_id
        ).first()

        items = db.query(PrescriptionItem).filter(
            PrescriptionItem.prescription_id == prescription.id
        ).all()

        items_list = []
        for item in items:
            medicine = db.query(Medicine).filter(
                Medicine.id == item.medicine_id
            ).first()
            items_list.append({
                "medicine_name": medicine.name if medicine else "Unknown",
                "frequency": item.frequency,
                "duration": item.duration,
                "quantity": item.quantity,
                "timing": item.timing
            })

        result.append({
            "id": prescription.id,
            "patient_id": prescription.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "status": prescription.status,
            "items": items_list,
            "created_at": prescription.created_at
        })

    return result


@router.get("/pending")
def get_pending_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Pharmacy sees pending prescriptions
    prescriptions = db.query(Prescription).filter(
        Prescription.clinic_id == current_user.clinic_id,
        Prescription.status == "pending"
    ).order_by(Prescription.created_at.desc()).all()

    result = []
    for prescription in prescriptions:
        patient = db.query(Patient).filter(
            Patient.patient_id == prescription.patient_id
        ).first()

        items = db.query(PrescriptionItem).filter(
            PrescriptionItem.prescription_id == prescription.id
        ).all()

        items_list = []
        for item in items:
            medicine = db.query(Medicine).filter(
                Medicine.id == item.medicine_id
            ).first()
            items_list.append({
                "medicine_id": item.medicine_id,
                "medicine_name": medicine.name if medicine else "Unknown",
                "frequency": item.frequency,
                "duration": item.duration,
                "quantity": item.quantity,
                "timing": item.timing,
                "price_per_unit": medicine.price_per_unit if medicine else 0,
                "total_price": item.quantity * medicine.price_per_unit if medicine else 0
            })

        result.append({
            "id": prescription.id,
            "patient_id": prescription.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "status": prescription.status,
            "items": items_list,
            "created_at": prescription.created_at
        })

    return result