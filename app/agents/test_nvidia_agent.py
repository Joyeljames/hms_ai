from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="writer/palmyra-med-70b-32k",
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.1
)

prompt = """You are a pharmacy assistant.

Prescription from doctor:
- Paracetamol 500mg: 3x/day, 5 days = 15 tablets
- Cetirizine 10mg: 1x/day, 5 days = 5 tablets
- Vitamin C 500mg: 1x/day, 5 days = 5 tablets

Current stock:
- Paracetamol 500mg: 100 tablets, ₹2.5/tab
- Cetirizine 10mg: 50 tablets, ₹5/tab
- Vitamin C 500mg: 8 tablets, ₹3/tab

Check stock availability and calculate bill.
Return JSON format."""

response = llm.invoke(prompt)
print("=== NVIDIA PALMYRA-MED ===")
print(response.content)