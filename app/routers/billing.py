from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bill, ClinicSettings, Prescription, Patient, User
from app.schemas import BillCreate, BillResponse, PaymentRequest
from app.core.auth import get_current_user
from app.models import PrescriptionItem, Medicine

router = APIRouter()

@router.post("/create",response_model=BillResponse)
def create_bill(
    bill:BillCreate,
    db:Session =Depends(get_db),
    current_user:User = Depends(get_current_user)
):

     # Get clinic settings for fees

    setting = db.query(ClinicSettings).filter(
        ClinicSettings.clinic_id == current_user.clinic_id
    ).first()

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Clinic fees not configured. Admin must set fees first."
        )

    # Get patient

    patient = db.query(Patient).filter(
        Patient.patient_id == bill.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Calculate registration fee
    registration_fee = setting.registration_fee if bill.is_new_patient else 0


        # Get medicine total from prescription
    medicine_total = 0
    if bill.prescription_id:
        prescription = db.query(Prescription).filter(
            Prescription.id == bill.prescription_id,
            Prescription.clinic_id == current_user.clinic_id
        ).first()

        if prescription and prescription.status == "dispensed":
            items = db.query(PrescriptionItem).filter(
                PrescriptionItem.prescription_id == bill.prescription_id
            ).all()

            for item in items:
                medicine = db.query(Medicine).filter(
                    Medicine.id == item.medicine_id
                ).first()
                if medicine:
                    medicine_total += item.quantity * medicine.price_per_unit

                       # Calculate total
    subtotal = registration_fee + setting.consultation_fee + medicine_total
    discount = bill.discount or 0
    total_amount = subtotal - discount

       # Create bill
    new_bill = Bill(
        clinic_id=current_user.clinic_id,
        patient_id=bill.patient_id,
        prescription_id=bill.prescription_id,
        appointment_id=bill.appointment_id,
        registration_fee=registration_fee,
        consultation_fee=setting.consultation_fee,
        medicine_total=medicine_total,
        discount=discount,
        total_amount=total_amount,
        status="pending"
    )
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)

    return {
        "id": new_bill.id,
        "patient_id": new_bill.patient_id,
        "patient_name": patient.name,
        "registration_fee": new_bill.registration_fee,
        "consultation_fee": new_bill.consultation_fee,
        "medicine_total": new_bill.medicine_total,
        "discount": new_bill.discount,
        "total_amount": new_bill.total_amount,
        "payment_method": new_bill.payment_method,
        "status": new_bill.status,
        "created_at": new_bill.created_at
    }


@router.post("/{bill_id}/pay")
def collect_payment(
    bill_id: int,
    payment: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate payment method
    valid_methods = ["cash", "upi", "card"]
    if payment.payment_method.lower() not in valid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method. Use: {valid_methods}"
        )

    # Find bill
    bill = db.query(Bill).filter(
        Bill.id == bill_id,
        Bill.clinic_id == current_user.clinic_id
    ).first()

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found"
        )

    if bill.status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Bill already paid"
        )

    # Update bill
    bill.status = "paid"
    bill.payment_method = payment.payment_method.lower()
    db.commit()
    db.refresh(bill)

    patient = db.query(Patient).filter(
        Patient.patient_id == bill.patient_id
    ).first()

    return {
        "message": "Payment collected successfully ✅",
        "bill_id": bill.id,
        "patient_id": bill.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "total_amount": bill.total_amount,
        "payment_method": bill.payment_method,
        "status": bill.status
    }

@router.get("/pending")
def get_pending_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bills = db.query(Bill).filter(
        Bill.clinic_id == current_user.clinic_id,
        Bill.status == "pending"
    ).order_by(Bill.created_at.desc()).all()

    result = []
    for bill in bills:
        patient = db.query(Patient).filter(
            Patient.patient_id == bill.patient_id
        ).first()

        result.append({
            "bill_id": bill.id,
            "patient_id": bill.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "registration_fee": bill.registration_fee,
            "consultation_fee": bill.consultation_fee,
            "medicine_total": bill.medicine_total,
            "discount": bill.discount,
            "total_amount": bill.total_amount,
            "created_at": bill.created_at
        })

    return result

@router.get("/today/revenue")
def get_today_revenue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from datetime import date
    from sqlalchemy import func

    today_bills = db.query(Bill).filter(
        Bill.clinic_id == current_user.clinic_id,
        Bill.status == "paid",
        func.date(Bill.created_at) == date.today()
    ).all()

    total_revenue = sum(bill.total_amount for bill in today_bills)
    total_patients = len(today_bills)

    return {
        "date": str(date.today()),
        "total_patients_billed": total_patients,
        "total_revenue": total_revenue,
        "bills": [
            {
                "bill_id": bill.id,
                "patient_id": bill.patient_id,
                "total_amount": bill.total_amount,
                "payment_method": bill.payment_method
            }
            for bill in today_bills
        ]
    }





