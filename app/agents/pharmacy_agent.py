from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import json

load_dotenv()

#pharmacy agent brain - groq(fast)

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)

# The Agent's notepad (State)
class PharmacyState(TypedDict):
    prescription_id: int
    patient_id: str
    patient_name: str
    prescription_items: list
    inventory: list
    stock_check: list
    out_of_stock: list
    alternatives: list
    total_bill: float
    pharmacist_action: str
    final_dispense: dict

# Node 1: Check stock for each prescribed medicine
def check_stock(state:PharmacyState):
    stock_check = []
    out_of_stock = []

    # Build inventory lookup
    inventory_map = {
        item["id"]: item
        for item in state["inventory"]
    }

    for item in state["prescription_items"]:
        medicine_id = item.get("medicine_id")
        required_qty = item.get("quantity", 0)

        medicine = inventory_map.get(medicine_id)

        if not medicine:
            out_of_stock.append({
                "medicine_name": item.get("medicine_name", "Unknown"),
                "required": required_qty,
                "available": 0,
                "reason": "Medicine not in inventory"
            })
            continue

        available = medicine.get("stock_quantity", 0)
        price = medicine.get("price_per_unit", 0)

        is_available = available >= required_qty

        stock_check.append({
            "medicine_id": medicine_id,
            "medicine_name": medicine.get("name"),
            "required": required_qty,
            "available": available,
            "sufficient": is_available,
            "price_per_unit": price,
            "subtotal": required_qty * price if is_available else 0
        })

        if not is_available:
            out_of_stock.append({
                "medicine_id": medicine_id,
                "medicine_name": medicine.get("name"),
                "required": required_qty,
                "available": available,
                "shortage": required_qty - available
            })

    state["stock_check"] = stock_check
    state["out_of_stock"] = out_of_stock

    return state

def suggest_alternatives(state: PharmacyState):
    if not state["out_of_stock"]:
        state["alternatives"] = []
        return state

    # Build available medicines list
    available_meds = [
        f"{m['name']} (stock: {m['stock_quantity']})"
        for m in state["inventory"]
        if m.get("stock_quantity", 0) > 0
    ]

    out_of_stock_names = [
        item["medicine_name"]
        for item in state["out_of_stock"]
    ]

    prompt = f"""You are a pharmacy assistant.

These medicines are OUT OF STOCK:
{", ".join(out_of_stock_names)}

Available medicines in clinic:
{", ".join(available_meds)}

STRICT RULES:
1. Suggest alternatives ONLY from the available list
2. Only suggest if therapeutically similar
3. If no suitable alternative exists, say "none"
4. Return ONLY valid JSON, no markdown

Return format:
{{
    "alternatives": [
        {{
            "original": "out of stock medicine name",
            "suggested": "alternative medicine name from list",
            "reason": "why this is a suitable alternative"
        }}
    ]
}}"""

    response = llm.invoke([
        SystemMessage(content="You are a pharmacy assistant. Return ONLY valid JSON. No markdown."),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        content = content.replace("```json", "").replace("```", "").strip()

        result = json.loads(content)
        state["alternatives"] = result.get("alternatives", [])
    except json.JSONDecodeError:
        state["alternatives"] = []

    return state

def calculate_bill(state: PharmacyState):
    total = 0

    for item in state["stock_check"]:
        if item["sufficient"]:
            total += item["subtotal"]

    state["total_bill"] = round(total, 2)
    return state


def pharmacist_review(state: PharmacyState):
    # This node pauses the graph
    # Waits for pharmacist confirmation
    return state

def dispense(state: PharmacyState):
    if state["pharmacist_action"] == "confirmed":
        state["final_dispense"] = {
            "prescription_id": state["prescription_id"],
            "patient_id": state["patient_id"],
            "patient_name": state["patient_name"],
            "items": state["stock_check"],
            "total_bill": state["total_bill"],
            "status": "dispensed"
        }
    return state

workflow = StateGraph(PharmacyState)
workflow.add_node("check_stock", check_stock)
workflow.add_node("suggest_alternatives", suggest_alternatives)
workflow.add_node("calculate_bill", calculate_bill)
workflow.add_node("review", pharmacist_review)
workflow.add_node("dispense", dispense)

workflow.set_entry_point("check_stock")
workflow.add_edge("check_stock", "suggest_alternatives")
workflow.add_edge("suggest_alternatives", "calculate_bill")
workflow.add_edge("calculate_bill", "review")

workflow.add_conditional_edges(
    "review",
    lambda state: state["pharmacist_action"],
    {
        "confirmed": "dispense",
        "rejected": END
    }
)
workflow.add_edge("dispense", END)

pharmacy_agent = workflow.compile()



def test_pharmacy_agent():
    initial_state = {
        "prescription_id": 1,
        "patient_id": "P-0001",
        "patient_name": "Ravi Kumar",
        "prescription_items": [
            {"medicine_id": 1, "medicine_name": "Paracetamol 500mg", "quantity": 15},
            {"medicine_id": 2, "medicine_name": "Cetirizine 10mg", "quantity": 5},
            {"medicine_id": 3, "medicine_name": "Vitamin C 500mg", "quantity": 20}
        ],
        "inventory": [
            {"id": 1, "name": "Paracetamol 500mg", "stock_quantity": 100, "price_per_unit": 2.5},
            {"id": 2, "name": "Cetirizine 10mg", "stock_quantity": 50, "price_per_unit": 5.0},
            {"id": 3, "name": "Vitamin C 500mg", "stock_quantity": 8, "price_per_unit": 3.0},
            {"id": 4, "name": "Zinc 50mg", "stock_quantity": 60, "price_per_unit": 4.0}
        ],
        "stock_check": [],
        "out_of_stock": [],
        "alternatives": [],
        "total_bill": 0.0,
        "pharmacist_action": "confirmed",
        "final_dispense": {}
    }

    result = pharmacy_agent.invoke(initial_state)

    print("=== PHARMACY AGENT RESULT ===\n")
    print("STOCK CHECK:")
    for item in result.get("stock_check", []):
        status = "✅" if item["sufficient"] else "❌"
        print(f"{status} {item['medicine_name']}: need {item['required']}, have {item['available']} — Rs {item['subtotal']}")

    print("\nOUT OF STOCK:")
    if result.get("out_of_stock"):
        for item in result["out_of_stock"]:
            print(f"❌ {item['medicine_name']}: short by {item.get('shortage', 0)}")
    else:
        print("None ✅")

    print("\nALTERNATIVES SUGGESTED:")
    if result.get("alternatives"):
        print(json.dumps(result["alternatives"], indent=2))
    else:
        print("None")

    print(f"\nTOTAL BILL: Rs {result.get('total_bill', 0)}")
    print(f"\nFINAL DISPENSE: {json.dumps(result.get('final_dispense', {}), indent=2)}")


if __name__ == "__main__":
    test_pharmacy_agent()