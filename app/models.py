from sqlalchemy import Column,String,Date,DateTime,Boolean,Integer,UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import UniqueConstraint

class Patient(Base):
    __tablename__ = "patients"

    id =    Column(Integer,primary_key=True,index=True)
    patient_id = Column(String(10),unique=True,nullable=False)
    clinic_id = Column(Integer,nullable=False)
    name = Column(String(150),nullable=False)
    phone = Column(String(15),nullable=False)
    gender = Column(String(10),nullable=False)
    date_of_birth = Column(Date,nullable=True)
    address = Column(String(255),nullable=True)
    created_at = Column(DateTime,server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,index=True)
    clinic_id = Column(Integer,nullable=True)
    name = Column(String(150),nullable=False)
    username = Column(String(150),nullable=False)
    password_hash = Column(String,nullable=False)
    role = Column(String(100),nullable=False)
    is_active = Column(Boolean,default=True,nullable=False)
    created_at = Column(DateTime,server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            'username',
            'clinic_id',
            name='unique_username_per_clinic'
        ),
    )

class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(200),nullable=False)
    address = Column(String(500),nullable=True)
    phone = Column(String(15),nullable=False)
    clinic_type = Column(String(50),default="general",nullable=False)
    plan = Column(String(30),default="basic",nullable=False)
    is_active = Column(Boolean,default=True,nullable=False)
    created_at = Column(DateTime,server_default=func.now())



class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, nullable=False)
    patient_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(50), default="waiting")
    token_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Visits(Base):
    __tablename__ = "visits"

    id = Column(Integer,primary_key=True,index=True)
    clinic_id = Column(Integer,nullable=False)
    patient_id = Column(String(10),nullable=False)
    doctor_id = Column(Integer,nullable=False)
    appointment_id = Column(Integer,nullable=False)
    complaint = Column(String(500),nullable=True)
    diagnosis = Column(String(500),nullable=True)
    notes = Column(String(1000),nullable=True)
    follow_up_date = Column(Date,nullable=True)
    created_at = Column(DateTime,server_default=func.now())



class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer,primary_key=True,index=True)
    clinic_id = Column(Integer,nullable=False)
    name = Column(String(200),nullable=False)
    unit = Column(String(50),nullable=False)
    price_per_unit = Column(Integer,nullable=False)
    stock_quantity = Column(Integer,nullable=False)
    low_stock_alert = Column(Integer,nullable=False)
    is_active = Column(Boolean,default=True)
    created_at = Column(DateTime,server_default=func.now())

class Prescription(Base):
     __tablename__ = "prescription"

     id = Column(Integer,primary_key=True,index=True)
     clinic_id = Column(Integer,nullable=False)
     patient_id = Column(String(10),nullable=False)
     doctor_id      = Column(Integer, nullable=False)
     visit_id       = Column(Integer, nullable=True)
     status         = Column(String(20), default="pending")
    # pending → dispensed → billed
     created_at     = Column(DateTime, server_default=func.now())



class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id              = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, nullable=False)
    medicine_id     = Column(Integer, nullable=False)
    frequency       = Column(Integer, nullable=False)
    duration        = Column(Integer, nullable=False)
    quantity        = Column(Integer, nullable=False)
    timing          = Column(String(50), nullable=True)
    # before food / after food