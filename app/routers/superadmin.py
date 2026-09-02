from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Clinic, User
from app.schemas import ClinicWithAdminCreate, ClinicResponse
from app.core.auth import get_current_user
from app.core.security import hash_password

router = APIRouter()

def require_superadmin(current_user:User):
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can perform this action"
        )

@router.post("/create/clinic")
def create_clinic(
    data:ClinicWithAdminCreate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    #check if superadmin
    require_superadmin(current_user)

    #create clinic

    new_clinic = Clinic(
        name=data.clinic.name,
        address=data.clinic.address,
        phone=data.clinic.phone,
        clinic_type=data.clinic.clinic_type,
        plan = data.clinic.plan
    )
    db.add(new_clinic)
    db.commit()
    db.refresh(new_clinic)

    #create admin user for clinic
    new_admin = User(
        clinic_id = new_clinic.id,
        name = data.admin.name,
        username = data.admin.username,
        password_hash = hash_password(data.admin.password),
        role = "admin",
        is_active = True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {
    "clinic_id": new_clinic.id,
    "clinic_name": new_clinic.name,
    "clinic_type": new_clinic.clinic_type,
    "phone": new_clinic.phone,
    "plan": new_clinic.plan,
    "is_active": new_clinic.is_active,
    "created_at": new_clinic.created_at,
    "admin_username": new_admin.username,
    "message": "Clinic created successfully ✅"
    }


@router.get("/clinics/all",response_model=list[ClinicResponse])
def get_all_clinics(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):

    require_superadmin(current_user)
    clinics = db.query(Clinic).all()
    return clinics

@router.put("/clinic/{clinic_id}/deactivate")

def deactivate_clinic(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_superadmin(current_user)

    clinic = db.query(Clinic).filter(
        Clinic.id == clinic_id
    ).first()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )

    clinic.is_active = False
    db.commit()

    return {
        "message": f"{clinic.name} deactivated ✅"
    }