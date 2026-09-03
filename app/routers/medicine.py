from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Medicine, User
from app.schemas import MedicineCreate, MedicineResponse, MedicineUpdate
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/add_medicine",response_model=MedicineResponse)
def add_medicine(
    medicine: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admin and pharmacist can add medicines
    if not current_user.role in ["admin","pharmacist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add medicines."
        )
    #check if medicine already exists in clinic
    existing = db.query(Medicine).filter(
        Medicine.name == medicine.name,
        Medicine.clinic_id == current_user.clinic_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine already exists in this clinic."
        )
    new_medicine = Medicine(
        clinic_id=current_user.clinic_id,
        name=medicine.name,
        unit=medicine.unit,
        price_per_unit=medicine.price_per_unit,
        stock_quantity=medicine.stock_quantity,
        low_stock_alert=medicine.low_stock_alert

    )

    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)

    return new_medicine

@router.get("/all",response_model=list[MedicineResponse])
def get_all_medicines(
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):

    medicines = db.query(Medicine).filter(
        Medicine.clinic_id == current_user.clinic_id,
        Medicine.is_active == True
    ).order_by(Medicine.name).all()

    return medicines

@router.get("/search",response_model=list[MedicineResponse])
def search_medicines(
    query:str,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    medicines = db.query(Medicine).filter(
        Medicine.clinic_id == current_user.clinic_id,
        Medicine.is_active == True,
        Medicine.name.ilike(f"%{query}%")
    ).all()

    return medicines

@router.get("/low_stock",response_model=list[MedicineResponse])
def get_low_stock_medicines(
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    medicines =db.query(Medicine).filter(
        Medicine.clinic_id == current_user.clinic_id,
        Medicine.is_active == True,
        Medicine.stock_quantity <= Medicine.low_stock_alert
    ).all()

    return medicines

@router.put("/{medicine_id}/update",response_model=MedicineResponse)
def update_medicine(
    medicine_id:int,
    updates:MedicineUpdate,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user)
):
    if current_user.role not in ["pharmacist","admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin and pharmacisit  can update medicines"
        )

    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id,
        Medicine.clinic_id == current_user.clinic_id
    ).first()

    if not medicine:
        raise HTTPException(
        status_code=404,
        detail="Medicine not found"
        )

    if updates.name is not None:
        medicine.name = updates.name
    if updates.unit is not None:
        medicine.unit = updates.unit
    if updates.price_per_unit is not None:
        medicine.price_per_unit  = updates.price_per_unit


    db.commit()
    db.refresh(medicine)

    return medicine
