from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse,ClinicFeesUpdate
from app.core.auth import get_current_user
from app.core.security import hash_password
from app.models import ClinicSettings



router = APIRouter()

valid_roles = ["admin", "doctor", "nurse", "receptionist","pharmacist"]

@router.post("/staff/create", response_model=UserResponse)
def create_staff(
    staff: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Check if admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create staff accounts"
        )
    #validate role
    if staff.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Valid roles are: {', '.join(valid_roles)}"
        )
     #Check username not taken in this clinic
    existing_user = db.query(User).filter(
        User.username == staff.username,
        User.clinic_id == current_user.clinic_id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken in this clinic"
        )
    # Create staff account
    new_staff = User(
        clinic_id=current_user.clinic_id,
        name=staff.name,
        username=staff.username,
        password_hash = hash_password(staff.password),
        role=staff.role,
        is_active=True
    )

    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)

    return new_staff



@router.get("/staff/all", response_model=list[UserResponse])
def get_all_staff(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #check if admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view staff accounts"
        )

    staff = db.query(User).filter(
        User.clinic_id == current_user.clinic_id
    ).all()
    return staff

@router.put("/staff/{staff_id}/deactivate", response_model=UserResponse)
def deactivate_staff(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #check if admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can deactivate staff accounts"
        )
    #find staff
    staff = db.query(User).filter(
        User.id == user_id,
        User.clinic_id == current_user.clinic_id
    ).first()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found"
        )
    # Cannot deactivate yourself
    if staff.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )
    #deactivate
    staff.is_active = False
    db.commit()
    db.refresh(staff)

    return staff

@router.post("/settings/fees")
def set_clinic_fees(
    fees: ClinicFeesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(403, "Only admin can set fees")

    settings = db.query(ClinicSettings).filter(
        ClinicSettings.clinic_id == current_user.clinic_id
    ).first()

    if settings:
        settings.registration_fee = fees.registration_fee
        settings.consultation_fee = fees.consultation_fee
        settings.follow_up_fee = fees.follow_up_fee
    else:
        settings = ClinicSettings(
            clinic_id=current_user.clinic_id,
            registration_fee=fees.registration_fee,
            consultation_fee=fees.consultation_fee,
            follow_up_fee=fees.follow_up_fee
        )
    db.add(settings)

    db.commit()
    db.refresh(settings)

    return {
        "message": "Fees updated successfully ✅",
        "registration_fee": settings.registration_fee,
        "consultation_fee": settings.consultation_fee,
        "follow_up_fee": settings.follow_up_fee
    }
