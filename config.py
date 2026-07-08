"""
config.py
Loads environment variables and sets up the Groq client.
Any file that needs to call the AI just imports `client` from here.
"""
 
import os
from dotenv import load_dotenv
from groq import Groq
 
load_dotenv()
 
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)