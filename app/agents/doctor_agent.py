from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import json
import requests


load_dotenv()

# The Agent's brain (Gemini)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


# The Agent's notepad (State)
class DoctorState(TypedDict):
    patient_id:str
    symptoms:str
    patient_history:list
    available_medicines:list
    diagnosis:str
    recommended_medicines:list
    interactions:str
    doctor_action:str
    final_prescription:dict

# Tool 1: Get patient history from HMS AI API
def get_patient_history(patient_id:str,token:str):
    response =requests.get(
        f"http://localhost:8000/visits/patient/{patient_id}/last2",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        return response.json()
    return []
# Tool 2: Get available medicines from HMS AI API
def get_available_medicines(token: str):
    response = requests.get(
        "http://localhost:8000/medicines/all",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return []


# Node 1: Analyze symptoms and get history
def analyze_and_fetch(state: DoctorState):
    # This will be called with token from the API endpoint
    # For now, history and medicines come from the state
    return state


# Node 2: Generate diagnosis and prescription
def generate_prescription(state: DoctorState):
    medicines_list = ", ".join(
        [m["name"] for m in state["available_medicines"]]
    )

    history_text = ""
    for visit in state["patient_history"]:
        history_text += f"Date: {visit.get('created_at', 'N/A')}, "
        history_text += f"Complaint: {visit.get('complaint', 'N/A')}, "
        history_text += f"Diagnosis: {visit.get('diagnosis', 'N/A')}\n"

    prompt = f"""You are a medical assistant helping a doctor.

Patient ID: {state['patient_id']}

Patient History:
{history_text if history_text else "No previous visits"}

Current Symptoms: {state['symptoms']}

Available medicines in clinic inventory ONLY:
{medicines_list}

STRICT RULES:
1. ONLY suggest medicines from the list above
2. NEVER suggest medicines not in the list
3. Give exact dosage and duration
4. Check drug interactions
5. Return ONLY valid JSON

Return this exact JSON format:
{{
    "diagnosis": "your diagnosis here",
    "medicines": [
        {{
            "name": "medicine name from list",
            "dosage": "dosage instructions",
            "frequency": 3,
            "duration": 5,
            "quantity": 15,
            "timing": "after food"
        }}
    ],
    "interactions": "interaction check result",
    "follow_up_days": 7,
    "notes": "additional notes for doctor"
}}"""

    response = llm.invoke([
        SystemMessage(content="You are a precise medical assistant. Return ONLY valid JSON. No markdown. No extra text."),
        HumanMessage(content=prompt)
    ])


    try:
        # Clean response
        content = response.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""

        # Remove markdown code blocks if present
        content = content.replace("```json", "").replace("```", "").strip()

        result = json.loads(content)
        state["diagnosis"] = result.get("diagnosis", "")
        state["recommended_medicines"] = result.get("medicines", [])
        state["interactions"] = result.get("interactions", "")
    except json.JSONDecodeError:
        state["diagnosis"] = "AI could not generate diagnosis. Doctor must diagnose manually."
        state["recommended_medicines"] = []
        state["interactions"] = "Could not check"

    return state

# Node 3: Human review (pause point)
def human_review(state: DoctorState):
    # This node pauses the graph
    # Waits for doctor to approve/edit/reject
    return state

# Node 4: Create prescription after approval
def create_prescription_node(state: DoctorState):
    if state["doctor_action"] == "approved":
        state["final_prescription"] = {
            "patient_id": state["patient_id"],
            "diagnosis": state["diagnosis"],
            "medicines": state["recommended_medicines"],
            "status": "approved_by_doctor"
        }
    return state

# Create the graph

workflow = StateGraph(DoctorState)

# Add nodes
workflow.add_node("analyze", analyze_and_fetch)
workflow.add_node("generate", generate_prescription)
workflow.add_node("review", human_review)
workflow.add_node("prescribe", create_prescription_node)

# Connect nodes
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "generate")
workflow.add_edge("generate", "review")


# After review — check doctor's action
workflow.add_conditional_edges(
    "review",
    lambda state: state["doctor_action"],
    {
        "approved": "prescribe",
        "rejected": END
    }
)
workflow.add_edge("prescribe", END)

# Compile the graph
doctor_agent = workflow.compile()


# Test function
def test_doctor_agent():
    # Simulate input
    initial_state = {
        "patient_id": "P-0001",
        "symptoms": "Fever 38.5°C, runny nose, headache for 2 days",
        "patient_history": [
            {
                "created_at": "2026-08-01",
                "complaint": "Cold and cough",
                "diagnosis": "Viral infection"
            }
        ],
        "available_medicines": [
            {"name": "Paracetamol 500mg"},
            {"name": "Cetirizine 10mg"},
            {"name": "Azithromycin 500mg"},
            {"name": "Vitamin C 500mg"},
            {"name": "Amoxicillin 500mg"}
        ],
        "diagnosis": "",
        "recommended_medicines": [],
        "interactions": "",
        "doctor_action": "approved",  # simulating approval
        "final_prescription": {}
    }

    # Run the agent
    result = doctor_agent.invoke(initial_state)

    print("=== DOCTOR AGENT RESULT ===")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Medicines: {json.dumps(result['recommended_medicines'], indent=2)}")
    print(f"Interactions: {result.get('interactions', 'N/A')}")
    print(f"Prescription: {json.dumps(result['final_prescription'], indent=2)}")

if __name__ == "__main__":
    test_doctor_agent()