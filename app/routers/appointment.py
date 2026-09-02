from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models import Appointment, Patient, User
from app.schemas import AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate
from app.core.auth import get_current_user
from datetime import date

router = APIRouter()




@router.post("/book")
def book_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == appointment.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Check doctor exists
    doctor = db.query(User).filter(
        User.id == appointment.doctor_id,
        User.clinic_id == current_user.clinic_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    # Check not already booked today
    existing = db.query(Appointment).filter(
        Appointment.patient_id == appointment.patient_id,
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today()
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Patient already has appointment today"
        )

    # Get next token number
    last_token = db.query(Appointment).filter(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today()
    ).count()

    # Create appointment
    new_appointment = Appointment(
        clinic_id=current_user.clinic_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        date=date.today(),
        status="waiting",
        token_number=last_token + 1
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return {
        "id": new_appointment.id,
        "patient_id": new_appointment.patient_id,
        "patient_name": patient.name,
        "doctor_id": new_appointment.doctor_id,
        "doctor_name": doctor.name,
        "date": new_appointment.date,
        "status": new_appointment.status,
        "token_number": new_appointment.token_number,
        "created_at": new_appointment.created_at
    }

@router.get("/today", response_model=list[AppointmentResponse])
def get_todays_appointments(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today()
    ).order_by(Appointment.token_number).all()

    return appointments

@router.put("/{appointment_id}/status")
def update_appointment_status(
    appointment_id:int,
    status_update:AppointmentStatusUpdate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)

):
    #validate status
    valid_statuses = ["waiting","with_doctor","done"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid statuses are: {valid_statuses}"
        )

    #find appointment
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.clinic_id == current_user.clinic_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    appointment.status = status_update.status.strip().lower()
    db.commit()
    db.refresh(appointment)

    return {
        "message": f"Appointment status updated to {appointment.status} ✅",
        "appointment_id": appointment.id,
        "token_number": appointment.token_number,
        "status": appointment.status
    }


@router.get("/stats/today")
def get_today_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total = db.query(Appointment).filter(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today()
    ).count()

    waiting = db.query(Appointment).filter(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today(),
        Appointment.status == "waiting"
    ).count()

    with_doctor = db.query(Appointment).filter(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today(),
        Appointment.status == "with_doctor"
    ).count()

    done = db.query(Appointment).filter(
        Appointment.clinic_id == current_user.clinic_id,
        Appointment.date == date.today(),
        Appointment.status == "done"
    ).count()

    return {
        "total_today": total,
        "waiting": waiting,
        "with_doctor": with_doctor,
        "done": done
    }
