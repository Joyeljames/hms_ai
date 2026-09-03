from pydantic import BaseModel
from typing import Optional
from datetime import date,datetime

class PatientCreate(BaseModel):

    name:str
    phone:str
    gender:str
    date_of_birth:Optional[date]=None
    address:Optional[str]=None

class PatientResponse(BaseModel):
    patient_id :str
    name:str
    phone:str
    gender:str
    date_of_birth:Optional[date]=None
    age:Optional[int]=None
    address:Optional[str]=None
    created_at:datetime

    class Config:

        from_attributes = True

class UserCreate(BaseModel):

    name:str
    username:str
    password:str
    role:str

class UserResponse(BaseModel):

    id:int
    name:str
    username:str
    role:str
    is_active:bool
    clinic_id:Optional[int]=None

    class Config:
        from_attributes = True


class ClinicCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: str
    clinic_type: str = "general"
    plan: str = "basic"


class ClinicResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    phone: str
    clinic_type: str
    plan: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AdminCreate(BaseModel):
    name: str
    username: str
    password: str

class AdminResponse(BaseModel):
    id:int
    name:str
    username:str
    role:str
    clini_id:int
    
    class Config:
        from_attributes = True


class ClinicWithAdminCreate(BaseModel):
    clinic: ClinicCreate
    admin: AdminCreate

class AppointmentCreate(BaseModel):
    patient_id:str
    doctor_id:int
   

class AppointmentResponse(BaseModel):
    id:int
    clinic_id:int
    patient_id:str
    doctor_id:int
    date:date
    status:str

    class Config:
        from_attributes = True

class AppointmentStatusUpdate(BaseModel):
    status: str

class VisitCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[int] = None
    complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None

class VisitResponse(BaseModel):
    id: int
    patient_id: str
    doctor_id: int
    appointment_id: int
    complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MedicineCreate(BaseModel):
    name: str
    unit: str
    price_per_unit: float
    stock_quantity: int
    low_stock_alert: int = 10

class MedicineResponse(BaseModel):
    id: int
    clinic_id: int
    name: str
    unit: str
    price_per_unit: float
    stock_quantity: int
    low_stock_alert: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
