"""
config.py
Loads environment variables and sets up the Groq client.
Any file that needs to call the AI just imports `client` from here.
"""
 
import os
from dotenv import load_dotenv
from groq import Groq
 
load_dotenv()
 
# ==========================================
# Groq client (unchanged)
# ==========================================
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
 
# ==========================================
# MySQL connection string
# ==========================================
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "careermomentum")
 
# Uses PyMySQL as the driver (pure Python, no extra system dependencies
# like the mysqlclient package needs).
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)