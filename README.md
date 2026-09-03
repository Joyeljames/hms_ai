# hms_ai# HMS AI 🏥

> AI-powered Hospital Management System for small clinics and hospitals in India.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What is HMS AI?

HMS AI replaces paper registers with an intelligent, AI-powered management system built specifically for small clinics and hospitals in India.

Most clinic software is either too expensive or too basic. HMS AI fills that gap — affordable, powerful, and AI-integrated.

---

## Features

### Core (Basic Plan)
- ✅ Unique patient ID (P-0001 format)
- ✅ Multi-role authentication (Admin, Doctor, Receptionist, Pharmacist)
- ✅ Patient registration and search
- ✅ Appointment booking with token queue system
- ✅ Doctor visit notes
- ✅ Prescription management
- ✅ Pharmacy module
- ✅ Billing and payment collection
- ✅ QR code prescriptions
- ✅ Data export (Excel)
- ✅ Multi-clinic support (one system, many clinics)

### AI Features (Premium Plan)
- 🤖 Visit history summarizer (last N visits on demand)
- 🤖 Medicine recommendation from clinic inventory only
- 🤖 Lab report AI analysis (photo or PDF upload)
- 🤖 Patient history search (pgvector RAG)

---

## Patient Flow

```
Reception → Doctor → Pharmacy → Billing
```

1. Receptionist registers patient → unique P-0001 ID generated
2. Appointment booked → token number assigned to queue
3. Doctor writes visit notes → prescription created and sent to pharmacy
4. Pharmacy receives prescription → medicines dispensed
5. Patient pays at reception → receipt generated

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 18 |
| ORM | SQLAlchemy |
| Authentication | JWT + bcrypt |
| AI/LLM | Groq API (Llama 3) |
| Embeddings | pgvector |
| Frontend | React + Tailwind CSS |
| Deployment | Docker + Cloudflare Tunnel |

---

## API Endpoints

### Authentication
```
POST /auth/login                     Login and get JWT token
```

### Patients
```
POST /patients/register              Register new patient
GET  /patients/search                Search by ID, phone, or name
GET  /patients/all                   Get all clinic patients
```

### Appointments
```
POST /appointments/book              Book appointment
GET  /appointments/today             Get today's queue
PUT  /appointments/{id}/status       Update appointment status
GET  /appointments/stats/today       Get today's stats
```

### Visits
```
POST /visits/create                  Create visit note
GET  /visits/patient/{id}            Get all patient visits
GET  /visits/patient/{id}/last2      Get last 2 visits
```

### Admin
```
POST /admin/staff/create             Create staff account
GET  /admin/staff/all                Get all staff
PUT  /admin/staff/{id}/deactivate    Deactivate staff account
```

### Superadmin
```
POST /superadmin/clinic/create       Create clinic + admin account
GET  /superadmin/clinics/all         Get all clinics
PUT  /superadmin/clinic/{id}/deactivate  Deactivate clinic
```

---

## Roles & Access

| Endpoint | Receptionist | Doctor | Pharmacist | Admin |
|---|---|---|---|---|
| Register patient | ✅ | ✅ | ❌ | ✅ |
| Book appointment | ✅ | ✅ | ❌ | ✅ |
| Write visit notes | ❌ | ✅ | ❌ | ✅ |
| Create prescription | ❌ | ✅ | ❌ | ✅ |
| Dispense medicine | ❌ | ❌ | ✅ | ✅ |
| Collect payment | ✅ | ❌ | ❌ | ✅ |
| Manage staff | ❌ | ❌ | ❌ | ✅ |
| Create clinic | ❌ | ❌ | ❌ | ❌ (superadmin only) |

---

## Plans

| Feature | Basic | Premium |
|---|---|---|
| Full HMS | ✅ | ✅ |
| Multi-role authentication | ✅ | ✅ |
| Patient management | ✅ | ✅ |
| Appointment token system | ✅ | ✅ |
| Doctor visit notes | ✅ | ✅ |
| Pharmacy + Billing | ✅ | ✅ |
| QR code prescriptions | ✅ | ✅ |
| Data export (Excel) | ✅ | ✅ |
| AI visit summarizer | ❌ | ✅ |
| Medicine recommendation AI | ❌ | ✅ |
| Lab report AI analysis | ❌ | ✅ |
| Patient history search (RAG) | ❌ | ✅ |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/JoyelJames/clinicflow-ai.git
cd clinicflow-ai

# Create conda environment
conda create -n clinicflow python=3.11
conda activate clinicflow

# Install dependencies
pip install -r requirements.txt

# Create database
psql -U postgres -c "CREATE DATABASE hms_db;"

# Run the server
uvicorn app.main:app --reload

# Open API docs
http://localhost:8000/docs
```

---

## Development Status

### Completed ✅
- [x] Project setup and PostgreSQL connection
- [x] Patient, User, Clinic, Appointment, Visit models
- [x] JWT authentication + bcrypt password hashing
- [x] Patient management (register, search, get all)
- [x] Admin staff management
- [x] Superadmin clinic management
- [x] Appointment system with token queue
- [x] Visit notes with doctor role check

### In Progress 🔨
- [ ] Medicine inventory management
- [ ] Prescription model and router
- [ ] Pharmacy module
- [ ] Billing system
- [ ] QR code generation
- [ ] Data export (Excel)
- [ ] AI features (Groq + RAG)
- [ ] React frontend
- [ ] Docker deployment

---

## About

HMS AI is being built for the 6,00,000+ small clinics and hospitals in India that still use paper registers. Most HMS software targets large hospitals with enterprise budgets. HMS AI targets small clinics that need powerful features at an affordable price.

**The problem:**
- 80% of small clinics in India use paper registers
- Enterprise HMS costs ₹8,000–20,000/month
- No AI-powered HMS at affordable price exists

**The solution:**
- HMS AI at ₹1,500–3,000/month
- Full AI integration at this price point
- Self-serve setup in 15 minutes
- Data always exportable — never locked in
- Supports Allopathy, Siddha, and Ayurveda

---

## Contact

Built by **Joyel J** — Nagercoil, Tamil Nadu 🇮🇳

- 💼 LinkedIn: [linkedin.com/in/joyel-j-793859339](https://linkedin.com/in/joyel-j-793859339)
- 📱 WhatsApp: [wa.me/918220397584](https://wa.me/918220397584)
- 📸 Instagram: [@neura_insights](https://instagram.com/neura_insights)
- 🐙 GitHub: [github.com/JoyelJames](https://github.com/JoyelJames)

---

*HMS AI — Built in Nagercoil, Tamil Nadu 🇮🇳*
*Replacing paper records with AI intelligence.*