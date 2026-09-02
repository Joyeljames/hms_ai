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