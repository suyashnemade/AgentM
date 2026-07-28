import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Enable LangSmith Tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
if api_key:
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGSMITH_API_KEY"] = api_key

project_name = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT", "data-cleaning-agent")
os.environ["LANGCHAIN_PROJECT"] = project_name
os.environ["LANGSMITH_PROJECT"] = project_name

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
)
