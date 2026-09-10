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

# Test the brain
response = llm.invoke("What is fever")
print(response.content)