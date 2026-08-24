from fastapi import FastAPI
from app.database import engine,Base
from app import models

# Create all tables
Base.metadata.create_all(bind = engine)


# Create FastAPI app
app = FastAPI(
    title="HMS AI",
    description="Hospital Management System",
    version="1.0.0"
)

# Root endpoint
@app.get("/")
def root():
    return {"message": "HMS AI is running ✅"}