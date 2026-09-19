from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# Create the brain (LLM
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)

prompt = """You are a medical assistant.

Patient: Male, 35 years old
Symptoms: Fever 38.5°C, runny nose, headache for 2 days

Available medicines in clinic:
Paracetamol 500mg, Cetirizine 10mg, Azithromycin 500mg, Vitamin C 500mg, Amoxicillin 500mg

1. Suggest diagnosis
2. Recommend medicines ONLY from list above
3. Give dosage and duration
4. Check drug interactions

Return in JSON format."""

# Test the brain
response = llm.invoke(prompt)
print("=== GROQ RESPONSE ===")
print(response.content)