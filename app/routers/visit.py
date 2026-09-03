from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Visits, Patient, User
from app.schemas import VisitCreate, VisitResponse
from app.core.auth import get_current_user


router = APIRouter()

@router.post("/create_visit",response_model=VisitResponse)
def create_visit(
    visit: VisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #only doctors and admins can create visits
    if current_user.role not in ["doctor","admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors and admins can create visits"
        )

    # Check if patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == visit.patient_id,
        Patient.clinic_id == current_user.clinic_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found in this clinic"
        )

    new_visit = Visits(
        clinic_id=current_user.clinic_id,
        patient_id=visit.patient_id,
        doctor_id=current_user.id,
        appointment_id=visit.appointment_id,
        complaint=visit.complaint,
        diagnosis=visit.diagnosis,
        notes=visit.notes,
        follow_up_date=visit.follow_up_date
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    return new_visit

@router.get("/patient/{patient_id}", response_model=list[VisitResponse])
def get_patient_visits(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    visits = db.query(Visits).filter(
        Visits.patient_id == patient_id,
        Visits.clinic_id == current_user.clinic_id
    ).order_by(Visits.created_at.desc()).all()

    return visits

@router.get("/patient/{patient_id}/last2", response_model=list[VisitResponse])
def get_last_2_visits(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    visits = db.query(Visits).filter(
        Visits.patient_id == patient_id,
        Visits.clinic_id == current_user.clinic_id
    ).order_by(Visits.created_at.desc()).limit(2).all()

    return visits