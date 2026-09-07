from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Prescription, PrescriptionItem, Medicine, Patient, User
from app.schemas import DispenseRequest,PharmacyDispenseRequest
from app.core.auth import get_current_user


router = APIRouter()


@router.get("/pending")
def get_pending_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["pharmacist", "admin"]:
        raise HTTPException(403, "Only pharmacist and admin  can view")

    prescriptions = db.query(Prescription).filter(
        Prescription.clinic_id == current_user.clinic_id,
        Prescription.status == "pending"
    ).order_by(Prescription.created_at.desc()).all()

    result = []
    for prescription in prescriptions:
        patient = db.query(Patient).filter(
            Patient.patient_id == prescription.patient_id
        ).first()

        result.append({
            "prescription_id": prescription.id,
            "patient_id": prescription.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "created_at": prescription.created_at
        })

    return result


@router.get("/prescription/{prescription_id}")
def view_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Pharmacist clicks to view what doctor prescribed
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.clinic_id == current_user.clinic_id
    ).first()

    if not prescription:
        raise HTTPException(404, "Prescription not found")

    patient = db.query(Patient).filter(
        Patient.patient_id == prescription.patient_id
    ).first()

    items = db.query(PrescriptionItem).filter(
        PrescriptionItem.prescription_id == prescription_id
    ).all()

    items_list = []
    for item in items:
        medicine = db.query(Medicine).filter(
            Medicine.id == item.medicine_id
        ).first()

        items_list.append({
            "prescription_item_id": item.id,
            "medicine_id": item.medicine_id,
            "medicine_name": medicine.name if medicine else "Unknown",
            "frequency": item.frequency,
            "duration": item.duration,
            "quantity": item.quantity,  # doctor's quantity
            "timing": item.timing,
            "in_stock": medicine.stock_quantity >= item.quantity if medicine else False,
            "available_stock": medicine.stock_quantity if medicine else 0
        })

    return {
        "prescription_id": prescription.id,
        "patient_id": prescription.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "status": prescription.status,
        "items": items_list
    }


@router.post("/dispense/{prescription_id}")
def dispense_prescription(
    prescription_id: int,
    dispense: PharmacyDispenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["pharmacist", "admin"]:
        raise HTTPException(403, "Only pharmacist can dispense")

    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.clinic_id == current_user.clinic_id
    ).first()

    if not prescription:
        raise HTTPException(404, "Prescription not found")

    if prescription.status != "pending":
        raise HTTPException(400, "Already dispensed")

    bill_items = []
    total_amount = 0

    # Process doctor's items with pharmacist's edited quantities
    for item in dispense.items:
        prescription_item = db.query(PrescriptionItem).filter(
            PrescriptionItem.id == item.prescription_item_id
        ).first()

        if not prescription_item:
            raise HTTPException(404, "Prescription item not found")

        medicine = db.query(Medicine).filter(
            Medicine.id == prescription_item.medicine_id,
            Medicine.clinic_id == current_user.clinic_id
        ).first()

        if not medicine:
            raise HTTPException(404, f"Medicine not found")

        # Use pharmacist's quantity (not doctor's original)
        final_quantity = item.quantity

        if medicine.stock_quantity < final_quantity:
            raise HTTPException(
                400,
                f"Insufficient stock for {medicine.name}. Available: {medicine.stock_quantity}"
            )

        # Reduce stock
        medicine.stock_quantity -= final_quantity
        db.commit()

        item_total = final_quantity * medicine.price_per_unit
        total_amount += item_total

        bill_items.append({
            "medicine_name": medicine.name,
            "quantity": final_quantity,
            "price_per_unit": medicine.price_per_unit,
            "total_price": item_total
        })

    # Process extra medicines added by pharmacist
    for extra in dispense.extra_items:
        medicine = db.query(Medicine).filter(
            Medicine.id == extra.medicine_id,
            Medicine.clinic_id == current_user.clinic_id
        ).first()

        if not medicine:
            raise HTTPException(404, "Extra medicine not found")

        if medicine.stock_quantity < extra.quantity:
            raise HTTPException(
                400,
                f"Insufficient stock for {medicine.name}"
            )

        medicine.stock_quantity -= extra.quantity
        db.commit()

        item_total = extra.quantity * medicine.price_per_unit
        total_amount += item_total

        bill_items.append({
            "medicine_name": medicine.name,
            "quantity": extra.quantity,
            "price_per_unit": medicine.price_per_unit,
            "total_price": item_total,
            "extra": True
        })

    # Update prescription status
    prescription.status = "dispensed"
    db.commit()

    patient = db.query(Patient).filter(
        Patient.patient_id == prescription.patient_id
    ).first()

    return {
        "prescription_id": prescription.id,
        "patient_id": prescription.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "status": "dispensed",
        "bill_items": bill_items,
        "medicine_total": total_amount,
        "message": "Dispensed successfully ✅"
    }