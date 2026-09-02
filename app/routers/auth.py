from fastapi import APIRouter,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
def login(
    form_data:OAuth2PasswordRequestForm=Depends(),
    db:Session=Depends(get_db)
):
    # Step 1: Find user by username
    user = db.query(User).filter(
        User.username==form_data.username
    ).first()

       # Step 2: Check if user exists
    if not user:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    # Step 3: Verify password
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled"
        )

     # Step 5: Create JWT token
    token = create_access_token({
        "user_id":user.id,
        "username":user.username,
        "role":user.role,
        "name":user.name,
        "clinic_id":user.clinic_id

    })
    # Step 6: Return token + role
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "clinic_id": user.clinic_id
    }
