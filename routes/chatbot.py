from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os

from prompts.prompts import SYSTEM_PROMPT
from website_info import WEBSITE_INFO

load_dotenv()

# Create a new Blueprint for the chatbot
chatbot_bp = Blueprint('chatbot', __name__)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

@chatbot_bp.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + WEBSITE_INFO),
            HumanMessage(content=user_message)
        ])
        
        return jsonify({"response": response.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500