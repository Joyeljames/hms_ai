"""
HMS AI — Admin Assistant
Tool-calling conversational agent for clinic business intelligence.

The AI decides which tools to call based on the question.
Tools query the real database, scoped to the admin's clinic_id.
Security (JWT + role check) is enforced by the endpoint before
set_context() is called.
"""

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from sqlalchemy import func
from datetime import date, timedelta
from dotenv import load_dotenv
import os
import json

from app.models import (
    Patient, Medicine, Bill, Appointment, User,
    Visits, Prescription, PrescriptionItem, ClinicSettings
)

load_dotenv()

# ─────────────────────────────────────────────
# BRAIN — Groq (fast, good at tool calling)
# ─────────────────────────────────────────────
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)


# ─────────────────────────────────────────────
# CONTEXT — set by the API endpoint before running
# ─────────────────────────────────────────────
_context = {
    "db": None,
    "clinic_id": None
}


def set_context(db, clinic_id):
    """Called by /ai/admin/ask after JWT + role verification.
    Gives the tools a database session scoped to one clinic."""
    _context["db"] = db
    _context["clinic_id"] = clinic_id


def _db():
    if _context["db"] is None:
        raise RuntimeError("Context not set. Call set_context() first.")
    return _context["db"]


def _clinic():
    return _context["clinic_id"]


def _date_range(days_back: int, period_days: int):
    """Returns (start_date, end_date) inclusive.
    days_back=0, period_days=1  -> today
    days_back=0, period_days=7  -> last 7 days including today
    days_back=30, period_days=30 -> the 30 days ending 30 days ago
    """
    end = date.today() - timedelta(days=days_back)
    start = end - timedelta(days=max(period_days - 1, 0))
    return start, end


# ═════════════════════════════════════════════
# TOOLS
# ═════════════════════════════════════════════

@tool
def get_revenue(days_back: int = 0, period_days: int = 1) -> str:
    """Get clinic revenue for any time period.

    days_back: 0 = ending today, 7 = ending 7 days ago, 30 = ending 30 days ago
    period_days: 1 = single day, 7 = one week, 30 = one month

    Examples:
      today            -> days_back=0,  period_days=1
      this week        -> days_back=0,  period_days=7
      this month       -> days_back=0,  period_days=30
      last month       -> days_back=30, period_days=30
      yesterday        -> days_back=1,  period_days=1

    Returns total revenue, bill count, payment method breakdown,
    and average bill value.
    """
    db = _db()
    start, end = _date_range(days_back, period_days)

    bills = db.query(Bill).filter(
        Bill.clinic_id == _clinic(),
        Bill.status == "paid",
        func.date(Bill.created_at) >= start,
        func.date(Bill.created_at) <= end
    ).all()

    total = sum(b.total_amount or 0 for b in bills)
    medicine_total = sum(b.medicine_total or 0 for b in bills)
    consultation_total = sum(b.consultation_fee or 0 for b in bills)
    registration_total = sum(b.registration_fee or 0 for b in bills)

    breakdown = {"cash": 0.0, "upi": 0.0, "card": 0.0}
    for b in bills:
        method = (b.payment_method or "cash").lower()
        if method in breakdown:
            breakdown[method] += (b.total_amount or 0)

    return json.dumps({
        "period_start": str(start),
        "period_end": str(end),
        "total_revenue": round(total, 2),
        "bills_count": len(bills),
        "average_bill": round(total / len(bills), 2) if bills else 0,
        "revenue_split": {
            "consultation": round(consultation_total, 2),
            "medicines": round(medicine_total, 2),
            "registration": round(registration_total, 2)
        },
        "payment_breakdown": {k: round(v, 2) for k, v in breakdown.items()}
    })


@tool
def get_patient_volume(days_back: int = 0, period_days: int = 1) -> str:
    """Get how many patients visited the clinic in a period.

    Use this for trends, busy-day analysis, and growth questions.
    Same date parameters as get_revenue.

    Returns appointment counts by status, new patient registrations,
    and daily average.
    """
    db = _db()
    start, end = _date_range(days_back, period_days)

    appts = db.query(Appointment).filter(
        Appointment.clinic_id == _clinic(),
        Appointment.date >= start,
        Appointment.date <= end
    ).all()

    new_patients = db.query(Patient).filter(
        Patient.clinic_id == _clinic(),
        func.date(Patient.created_at) >= start,
        func.date(Patient.created_at) <= end
    ).count()

    statuses = {"waiting": 0, "with_doctor": 0, "done": 0}
    for a in appts:
        s = (a.status or "waiting").lower()
        if s in statuses:
            statuses[s] += 1

    days = max((end - start).days + 1, 1)

    return json.dumps({
        "period_start": str(start),
        "period_end": str(end),
        "total_appointments": len(appts),
        "by_status": statuses,
        "new_patients_registered": new_patients,
        "daily_average": round(len(appts) / days, 1)
    })


@tool
def get_stock_report(only_low: bool = False) -> str:
    """Get the medicine inventory report.

    only_low: False = every active medicine,
              True  = only medicines at or below their alert level

    Returns each medicine's stock, price, stock value, and whether
    it needs restocking, plus the total inventory value.
    """
    db = _db()

    query = db.query(Medicine).filter(
        Medicine.clinic_id == _clinic(),
        Medicine.is_active == True
    )

    if only_low:
        query = query.filter(
            Medicine.stock_quantity <= Medicine.low_stock_alert
        )

    medicines = query.order_by(Medicine.stock_quantity).all()

    items = []
    total_value = 0.0

    for m in medicines:
        value = (m.stock_quantity or 0) * (m.price_per_unit or 0)
        total_value += value
        items.append({
            "name": m.name,
            "stock": m.stock_quantity,
            "unit": m.unit,
            "price_per_unit": m.price_per_unit,
            "alert_level": m.low_stock_alert,
            "needs_restock": (m.stock_quantity or 0) <= (m.low_stock_alert or 0),
            "stock_value": round(value, 2)
        })

    return json.dumps({
        "medicine_count": len(items),
        "total_inventory_value": round(total_value, 2),
        "medicines": items
    })


@tool
def get_restock_estimate() -> str:
    """Get a restocking plan: which medicines are below their alert
    level, how many units to order to reach a healthy level,
    and the estimated cost for each and in total.

    Use this when the admin asks what to reorder or how much
    restocking will cost.
    """
    db = _db()

    medicines = db.query(Medicine).filter(
        Medicine.clinic_id == _clinic(),
        Medicine.is_active == True,
        Medicine.stock_quantity <= Medicine.low_stock_alert
    ).all()

    plan = []
    total_cost = 0.0

    for m in medicines:
        alert = m.low_stock_alert or 10
        current = m.stock_quantity or 0
        # restock to 3x the alert level as a healthy buffer
        target = alert * 3
        order_qty = max(target - current, 0)
        cost = order_qty * (m.price_per_unit or 0)
        total_cost += cost

        plan.append({
            "name": m.name,
            "current_stock": current,
            "alert_level": alert,
            "suggested_order_qty": order_qty,
            "unit_price": m.price_per_unit,
            "estimated_cost": round(cost, 2)
        })

    return json.dumps({
        "items_needing_restock": len(plan),
        "total_estimated_cost": round(total_cost, 2),
        "restock_plan": plan
    })


@tool
def get_top_medicines(days_back: int = 30) -> str:
    """Get the most prescribed medicines over the last N days.

    days_back: how many days to look back (default 30)

    Use this to decide what to stock more of, or to see which
    medicines actually generate revenue.
    """
    db = _db()
    start = date.today() - timedelta(days=days_back)

    prescriptions = db.query(Prescription).filter(
        Prescription.clinic_id == _clinic(),
        func.date(Prescription.created_at) >= start
    ).all()

    if not prescriptions:
        return json.dumps({
            "period_days": days_back,
            "message": "No prescriptions in this period",
            "top_medicines": []
        })

    prescription_ids = [p.id for p in prescriptions]

    items = db.query(PrescriptionItem).filter(
        PrescriptionItem.prescription_id.in_(prescription_ids)
    ).all()

    tally = {}
    for item in items:
        med = db.query(Medicine).filter(
            Medicine.id == item.medicine_id
        ).first()
        if not med:
            continue
        if med.name not in tally:
            tally[med.name] = {
                "name": med.name,
                "times_prescribed": 0,
                "total_units": 0,
                "current_stock": med.stock_quantity,
                "revenue": 0.0
            }
        tally[med.name]["times_prescribed"] += 1
        tally[med.name]["total_units"] += (item.quantity or 0)
        tally[med.name]["revenue"] += (item.quantity or 0) * (med.price_per_unit or 0)

    ranked = sorted(
        tally.values(),
        key=lambda x: x["total_units"],
        reverse=True
    )

    for r in ranked:
        r["revenue"] = round(r["revenue"], 2)

    return json.dumps({
        "period_days": days_back,
        "total_prescriptions": len(prescriptions),
        "top_medicines": ranked[:10]
    })


@tool
def get_staff_report() -> str:
    """Get all staff members with their roles and active status,
    plus how many patients each doctor has seen in the last 30 days.

    Use this for workload, hiring, and team questions.
    """
    db = _db()
    start = date.today() - timedelta(days=30)

    staff = db.query(User).filter(
        User.clinic_id == _clinic()
    ).all()

    result = []
    for s in staff:
        entry = {
            "name": s.name,
            "username": s.username,
            "role": s.role,
            "active": s.is_active
        }
        if s.role in ("doctor", "admin"):
            seen = db.query(Appointment).filter(
                Appointment.clinic_id == _clinic(),
                Appointment.doctor_id == s.id,
                Appointment.date >= start
            ).count()
            entry["patients_seen_last_30_days"] = seen
        result.append(entry)

    role_counts = {}
    for s in staff:
        if s.is_active:
            role_counts[s.role] = role_counts.get(s.role, 0) + 1

    return json.dumps({
        "total_staff": len(staff),
        "active_by_role": role_counts,
        "staff": result
    })


@tool
def get_consultation_fees() -> str:
    """Get the clinic's configured fees: registration fee,
    consultation fee, and follow-up fee.

    Use this for pricing questions or revenue projections.
    """
    db = _db()

    settings = db.query(ClinicSettings).filter(
        ClinicSettings.clinic_id == _clinic()
    ).first()

    if not settings:
        return json.dumps({
            "configured": False,
            "message": "Clinic fees not configured yet. Admin must set them."
        })

    return json.dumps({
        "configured": True,
        "registration_fee": settings.registration_fee,
        "consultation_fee": settings.consultation_fee,
        "follow_up_fee": settings.follow_up_fee
    })


@tool
def get_unpaid_bills() -> str:
    """Get all unpaid bills with patient names, amounts, and how
    many days they have been outstanding.

    Use this for cash-flow and collections questions.
    """
    db = _db()

    bills = db.query(Bill).filter(
        Bill.clinic_id == _clinic(),
        Bill.status == "pending"
    ).order_by(Bill.created_at).all()

    result = []
    total = 0.0

    for b in bills:
        patient = db.query(Patient).filter(
            Patient.patient_id == b.patient_id
        ).first()

        days_old = 0
        if b.created_at:
            days_old = (date.today() - b.created_at.date()).days

        total += (b.total_amount or 0)

        result.append({
            "bill_id": b.id,
            "patient_id": b.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "patient_phone": patient.phone if patient else None,
            "amount": b.total_amount,
            "days_outstanding": days_old
        })

    return json.dumps({
        "unpaid_count": len(result),
        "total_outstanding": round(total, 2),
        "bills": result
    })


@tool
def get_missed_followups() -> str:
    """Get patients whose follow-up date has passed but who have
    not returned to the clinic.

    Use this for patient recall and retention questions.
    """
    db = _db()
    today = date.today()

    visits = db.query(Visits).filter(
        Visits.clinic_id == _clinic(),
        Visits.follow_up_date != None,
        Visits.follow_up_date < today
    ).all()

    result = []
    for v in visits:
        # did the patient come back after the follow-up date?
        returned = db.query(Visits).filter(
            Visits.clinic_id == _clinic(),
            Visits.patient_id == v.patient_id,
            func.date(Visits.created_at) > v.follow_up_date
        ).first()

        if returned:
            continue

        patient = db.query(Patient).filter(
            Patient.patient_id == v.patient_id
        ).first()

        result.append({
            "patient_id": v.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "patient_phone": patient.phone if patient else None,
            "last_diagnosis": v.diagnosis,
            "follow_up_was_due": str(v.follow_up_date),
            "days_overdue": (today - v.follow_up_date).days
        })

    return json.dumps({
        "missed_followups_count": len(result),
        "patients": result
    })


@tool
def search_patient(query: str) -> str:
    """Search for patients by name, phone number, or patient ID.

    query: any part of the name, phone, or ID (e.g. "ravi", "9876", "P-0001")

    Returns up to 5 matching patients.
    """
    db = _db()

    patients = db.query(Patient).filter(
        Patient.clinic_id == _clinic()
    ).filter(
        (Patient.name.ilike(f"%{query}%")) |
        (Patient.phone.ilike(f"%{query}%")) |
        (Patient.patient_id.ilike(f"%{query}%"))
    ).limit(5).all()

    return json.dumps([
        {
            "patient_id": p.patient_id,
            "name": p.name,
            "phone": p.phone,
            "gender": p.gender,
            "address": p.address,
            "registered_on": str(p.created_at.date()) if p.created_at else None
        }
        for p in patients
    ])


@tool
def get_patient_full_record(patient_id: str) -> str:
    """Get the complete record for one patient: all visits with
    diagnoses, all prescriptions, and all bills.

    patient_id: the patient's ID, e.g. "P-0001"

    Use this when the admin asks about a specific patient's history.
    """
    db = _db()

    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.clinic_id == _clinic()
    ).first()

    if not patient:
        return json.dumps({"error": f"Patient {patient_id} not found"})

    visits = db.query(Visits).filter(
        Visits.patient_id == patient_id,
        Visits.clinic_id == _clinic()
    ).order_by(Visits.created_at.desc()).all()

    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient_id,
        Prescription.clinic_id == _clinic()
    ).order_by(Prescription.created_at.desc()).all()

    bills = db.query(Bill).filter(
        Bill.patient_id == patient_id,
        Bill.clinic_id == _clinic()
    ).order_by(Bill.created_at.desc()).all()

    total_spent = sum(b.total_amount or 0 for b in bills if b.status == "paid")

    return json.dumps({
        "patient": {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "phone": patient.phone,
            "gender": patient.gender,
            "address": patient.address
        },
        "total_visits": len(visits),
        "total_spent": round(total_spent, 2),
        "visits": [
            {
                "date": str(v.created_at.date()) if v.created_at else None,
                "complaint": v.complaint,
                "diagnosis": v.diagnosis,
                "follow_up_date": str(v.follow_up_date) if v.follow_up_date else None
            }
            for v in visits[:10]
        ],
        "prescriptions_count": len(prescriptions),
        "bills": [
            {
                "bill_id": b.id,
                "amount": b.total_amount,
                "status": b.status,
                "date": str(b.created_at.date()) if b.created_at else None
            }
            for b in bills[:10]
        ]
    })


# ═════════════════════════════════════════════
# BIND TOOLS
# ═════════════════════════════════════════════

tools = [
    get_revenue,
    get_patient_volume,
    get_stock_report,
    get_restock_estimate,
    get_top_medicines,
    get_staff_report,
    get_consultation_fees,
    get_unpaid_bills,
    get_missed_followups,
    search_patient,
    get_patient_full_record
]

tools_map = {t.name: t for t in tools}

llm_with_tools = llm.bind_tools(tools)


# ═════════════════════════════════════════════
# REASONING PROMPT
# ═════════════════════════════════════════════

SYSTEM_PROMPT = """You are a business analyst for a small clinic in India.
You do not just report numbers — you ANALYSE the data and ADVISE the admin.

HOW TO THINK:
1. Work out what the admin actually wants to know, not just the literal words.
2. Decide what data you need. Most real questions need MORE THAN ONE tool.
3. Call the tools.
4. If the results raise a new question, call MORE tools before answering.
5. Reason over everything you gathered, then give a clear recommendation.

WORKED EXAMPLES OF REASONING:

Admin: "What stock do I need to refill?"
  -> get_restock_estimate()   (what is low and what it costs)
  -> get_top_medicines(30)    (what actually sells)
  -> get_revenue(0, 30)       (can they afford it)
  Answer: a prioritised list. Restock the fast-moving items first,
  mention the total cost against monthly revenue, and suggest skipping
  slow-moving items that are low but rarely prescribed.

Admin: "Can I appoint a new staff member?"
  -> get_revenue(0, 30)       (monthly income)
  -> get_patient_volume(0, 30)(workload)
  -> get_staff_report()       (current team and their load)
  -> get_consultation_fees()  (unit economics)
  Answer: yes or no, with the numbers that justify it — is the team
  overloaded, and does revenue support another salary.

Admin: "How is the clinic doing?"
  -> get_revenue(0, 30) and get_revenue(30, 30)  (this month vs last)
  -> get_patient_volume(0, 30) and get_patient_volume(30, 30)
  -> get_stock_report(only_low=True)
  -> get_unpaid_bills()
  Answer: what is improving, what is declining, and the single most
  important thing to fix.

Admin: "Are we losing patients?"
  -> get_missed_followups()
  -> get_patient_volume for two periods to compare
  Answer: how many patients did not return, who to call back first.

RULES:
- NEVER invent a number. Every figure must come from a tool result.
- Always end with a clear recommendation or next action, not just data.
- Use Rs for money and Indian number formatting.
- Flag risks plainly: low stock, unpaid bills, falling revenue, overdue follow-ups.
- If the data needed does not exist, say so — do not guess.
- Keep the answer tight. Tables for lists, short paragraphs for advice.
"""


# ═════════════════════════════════════════════
# CONVERSATION LOOP (with memory)
# ═════════════════════════════════════════════

conversation_history = []


def ask_admin_assistant(question: str, reset: bool = False, verbose: bool = True):
    """Ask the admin assistant a question.

    reset: True clears the conversation memory
    verbose: True prints which tools the AI decided to call
    """
    global conversation_history

    if reset:
        conversation_history = []

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(conversation_history)
    messages.append(HumanMessage(content=question))

    max_rounds = 8

    for i in range(max_rounds):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # AI is done thinking — it wrote an answer
        if not response.tool_calls:
            answer = response.content or "I could not generate an answer."

            conversation_history.append(HumanMessage(content=question))
            conversation_history.append(response)
            # keep the last 5 exchanges only
            conversation_history = conversation_history[-10:]

            return answer

        if verbose:
            print(f"🔧 Round {i+1}: calling {len(response.tool_calls)} tool(s)")

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if verbose:
                print(f"   -> {tool_name}({tool_args})")

            selected_tool = tools_map.get(tool_name)

            if not selected_tool:
                tool_result = json.dumps({"error": f"Unknown tool {tool_name}"})
            else:
                try:
                    tool_result = selected_tool.invoke(tool_args)
                except Exception as e:
                    tool_result = json.dumps({"error": str(e)})

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
            )

    return "That question needed too many steps. Please ask something more specific."


def clear_conversation():
    """Reset the assistant's memory."""
    global conversation_history
    conversation_history = []