from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Patient, User
from app.schemas import PatientCreate, PatientResponse
from app.core.auth import get_current_user
from datetime import date

router = APIRouter()
def calculate_age(dob):
      if dob is None:
            return None
      today = date.today()
      return today.year - dob.year
      
@router.post("/register_patients",response_model=PatientResponse)
def register_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
     # 1. Check duplicate phone
     existing = db.query(Patient).filter(
          Patient.phone == patient.phone,
          Patient.clinic_id == current_user.clinic_id
     ).first()
     if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient with this phone number already exists"
            )

      # 2. Create patient with TEMP id
     new_patient = Patient(
                patient_id="TEMP",
                clinic_id=current_user.clinic_id,
                name=patient.name,
                phone=patient.phone,
                gender=patient.gender,
                date_of_birth=patient.date_of_birth,
                address=patient.address
            )

     # 3. Save to database
     db.add(new_patient)
     db.commit()
     db.refresh(new_patient)
# 4. Generate patient_id from auto id
     new_patient.patient_id = f"P-{new_patient.id:04d}"
     db.commit()
     db.refresh(new_patient)

     new_patient.age = calculate_age(new_patient.date_of_birth)

     return new_patient


@router.get("/search_patients",response_model=PatientResponse)
def search_patients(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
      #search patients by name or phone
      patient = db.query(Patient).filter(
            Patient.clinic_id == current_user.clinic_id,
            or_(
                Patient.patient_id == query,
                Patient.name.ilike(f"%{query}%"),
                Patient.phone == query
            )
      ).first()

      if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )

      return {

            "patient_id": patient.patient_id,
            "name": patient.name,
            "phone": patient.phone,
            "gender": patient.gender,
            "date_of_birth": patient.date_of_birth,
            "age": calculate_age(patient.date_of_birth),
            "address": patient.address,
            "created_at": patient.created_at
            
      }

@router.get("/all_patients", response_model=list[PatientResponse])
def get_all_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patients = db.query(Patient).filter(
        Patient.clinic_id == current_user.clinic_id
    ).order_by(Patient.created_at.desc()).all()

    return [
        {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "phone": patient.phone,
            "gender": patient.gender,
            "date_of_birth": patient.date_of_birth,
            "age": calculate_age(patient.date_of_birth),
            "address": patient.address,
            "created_at": patient.created_at
        }
        for patient in patients
    ]
        
    


