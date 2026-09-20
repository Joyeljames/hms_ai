from fastapi import FastAPI
from app.database import engine,Base
from app import models
from app.routers import auth as auth_router
from app.routers import patient as patient_router
from app.routers import admin as admin_router
from app.routers import superadmin as superadmin_router
from app.routers import appointment as appointment_router
from app.routers import visit as visit_router
from app.routers import medicine as medicine_router
from app.routers import prescription as prescription_router
from app.routers import pharmacy as pharmacy_router
from app.routers import billing as billing_router
from app.routers import export as export_router
from app.routers import ai_agent as ai_agent_router
from fastapi.middleware.cors import CORSMiddleware
# Create all tables
Base.metadata.create_all(bind = engine)



# Create FastAPI app
app = FastAPI(
    title="HMS AI",
    description="Hospital Management System",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


app.include_router(
    visit_router.router,
    prefix="/visits",
    tags=["Visits"]
)

app.include_router(
    medicine_router.router,
    prefix="/medicines",
    tags=["Medicines"]
)

app.include_router(
    prescription_router.router,
    prefix="/prescriptions",
    tags=["Prescriptions"]
)



app.include_router(
    pharmacy_router.router,
    prefix="/pharmacy",
    tags=["Pharmacy"]
)

app.include_router(
    billing_router.router,
    prefix="/billing",
    tags=["Billing"]
)

app.include_router(
    export_router.router,
    prefix="/export",
    tags=["Export"]
)

from app.routers import ai_agent as ai_agent_router

app.include_router(
    ai_agent_router.router,
    prefix="/ai",
    tags=["AI Agents"]
)




# Root endpoint
@app.get("/")
def root():
    return {"message": "HMS AI is running ✅"}

