from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os


load_dotenv()


llm = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash",
    temperature = 0.1,
    google_api_key = os.getenv("GOOGLE_API_KEY")
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



response = llm.invoke(prompt)
print("=== GEMINI RESPONSE ===")
print(response.content)