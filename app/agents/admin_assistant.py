from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
import os
import json

load_dotenv()

#admin assistant brain

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)

# ─── FAKE DATA (replaced with real API on Day 19) ───

FAKE_REVENUE = {
    "date": "2026-09-19",
    "total_revenue": 12450.0,
    "total_patients_billed": 34,
    "payment_breakdown": {"cash": 8200, "upi": 3750, "card": 500}
}

FAKE_STATS = {
    "total_today": 47,
    "waiting": 12,
    "with_doctor": 1,
    "done": 34
}

FAKE_LOW_STOCK = [
    {"name": "Paracetamol 500mg", "stock": 8, "alert_level": 20},
    {"name": "Vitamin C 500mg", "stock": 5, "alert_level": 15},
    {"name": "Zinc 50mg", "stock": 3, "alert_level": 10}
]

FAKE_PENDING_BILLS = [
    {"bill_id": 12, "patient_name": "Meena Devi", "amount": 450.0},
    {"bill_id": 15, "patient_name": "Arjun S", "amount": 320.0}
]

FAKE_PATIENTS = [
    {"patient_id": "P-0001", "name": "Ravi Kumar", "phone": "9876543210", "age": 35},
    {"patient_id": "P-0002", "name": "Meena Devi", "phone": "9876543211", "age": 28}
]

FAKE_STAFF = [
    {"name": "Dr. Melbin Moses", "role": "admin", "active": True},
    {"name": "Lakshmi R", "role": "receptionist", "active": True},
    {"name": "Suresh K", "role": "pharmacist", "active": True}
]


#tools

@tool
def get_today_revenue() ->str:
    """Get today's total revenue, number of patients billed,
    and payment method breakdown for the clinic."""
    return json.dumps(FAKE_REVENUE)

@tool
def get_today_stats()->str:
    """Get today's patient queue statistics — total patients,
    how many are waiting, how many are with the doctor,
    and how many are done."""
    return json.dumps(FAKE_STATS)

@tool
def get_low_stock()->str:
    """Get the list of medicines that are running low on stock
    and need to be restocked."""
    return json.dumps(FAKE_LOW_STOCK)

@tool
def get_pending_bills() -> str:
    """Get the list of bills that have not been paid yet,
    with patient names and amounts."""
    return json.dumps(FAKE_PENDING_BILLS)


@tool
def search_patient(query: str) -> str:
    """Search for a patient by name, phone number, or patient ID.
    Returns matching patient details."""
    results = [
        p for p in FAKE_PATIENTS
        if query.lower() in p["name"].lower()
        or query in p["phone"]
        or query.upper() == p["patient_id"]
    ]
    return json.dumps(results)

@tool
def get_staff_list() -> str:
    """Get the list of all staff members in the clinic
    with their roles and active status."""
    return json.dumps(FAKE_STAFF)


# All available tools
tools = [
    get_today_revenue,
    get_today_stats,
    get_low_stock,
    get_pending_bills,
    search_patient,
    get_staff_list
]

# Tool lookup map
tools_map = {t.name: t for t in tools}


# Give the LLM access to tools
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are an assistant for a clinic admin in India.

You help the admin understand their clinic's performance.

RULES:
1. Use tools to get real data — never make up numbers
2. For VAGUE questions like "anything to worry about?" or
   "how are we doing?" — call MULTIPLE tools to get a
   complete picture (revenue, stats, low stock, pending bills)
3. ALWAYS write a final answer in plain text after getting tool results
4. Give short, clear answers
5. Use Indian Rupees (Rs) for money
6. Point out problems clearly — low stock, unpaid bills"""

def ask_admin_assistant(question: str):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question)
    ]

    max_iterations = 5

    for i in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # No tools requested — AI is done
        if not response.tool_calls:
            if response.content:
                return response.content
            return "I could not generate an answer."

        print(f"🔧 Round {i+1}: calling {len(response.tool_calls)} tool(s):")

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            print(f"   → {tool_name}({tool_args})")

            selected_tool = tools_map[tool_name]
            tool_result = selected_tool.invoke(tool_args)

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
            )

    return "Reached maximum tool calls without a final answer."

def test_admin_assistant():
    questions = [
        "What's today's revenue?",
        "How many patients are still waiting?",
        "Which medicines are running low?",
        "Is there anything I should worry about today?"
    ]

    for q in questions:
        print("\n" + "="*60)
        print(f"❓ ADMIN: {q}")
        print("="*60)
        answer = ask_admin_assistant(q)
        print(f"\n🤖 ASSISTANT: {answer}")


if __name__ == "__main__":
    test_admin_assistant()