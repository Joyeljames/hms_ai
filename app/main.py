from fastapi import FastAPI
from app.database import engine,Base
from app import models
from app.routers import auth as auth_router
from app.routers import patient as patient_router
from app.routers import admin as admin_router
from app.routers import superadmin as superadmin_router
from app.routers import appointment as appointment_router

# Create all tables
Base.metadata.create_all(bind = engine)


# Create FastAPI app
app = FastAPI(
    title="HMS AI",
    description="Hospital Management System",
    version="1.0.0"
)

app.include_router(
    auth_router.router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    patient_router.router,
    prefix="/patients",
    tags=["Patients"]

)
app.include_router(
    admin_router.router,
    prefix="/admin",
    tags=["Admin"]
)
app.include_router(
    superadmin_router.router,
    prefix="/superadmin",
    tags=["Superadmin"]
)

app.include_router(
    appointment_router.router,
    prefix="/appointments",
    tags=["Appointments"]
)


# Root endpoint
@app.get("/")
def root():
    return {"message": "HMS AI is running ✅"}