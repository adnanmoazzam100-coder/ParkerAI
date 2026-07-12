import os
from dotenv import load_dotenv

print("Checking directory...")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Does .env file exist here? {os.path.exists('.env')}\n")

# Try to load the environment variables
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

print("--- Environmental Variables Scan ---")
if groq_key:
    print(f"GROQ_API_KEY found! Starts with: {groq_key[:8]}... Length: {len(groq_key)}")
else:
    print("GROQ_API_KEY is completely missing or empty.")

if tavily_key:
    print(f"TAVILY_API_KEY found! Starts with: {tavily_key[:8]}... Length: {len(tavily_key)}")
else:
    print("TAVILY_API_KEY is completely missing or empty.")