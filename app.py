from flask import Flask, render_template, request, jsonify, session
from langchain_google_genai import ChatGoogleGenerativeAI
from worker_agents import (
    verify_customer_details,
    perform_underwriting,
    generate_sanction_letter_pdf
)
import json
import os
import requests

app = Flask(__name__, template_folder="templates")
app.secret_key = "supersecretkey123"   # needed for session


with open("config.json") as f:
    config = json.load(f)

llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=config["api_key"],
    temperature=0.7,
    convert_system_message_to_human=True
)

def save_chat_to_firebase(user_msg, bot_msg):
    try:
        conversation = {
            "user": user_msg,
            "bot": bot_msg
        }

        url = config["realtime_url"].rstrip("/") + "/conversations.json"

        requests.post(url, json=conversation)
    except Exception as e:
        print("Firebase save error:", e)

def init_state():
    if "step" not in session:
        session["step"] = "start"
        session["details"] = {}
        session["messages"] = [
            {"role": "assistant", "content": "Welcome! How can I help you today?"}
        ]

@app.route("/")
def chat():
    init_state()
    return render_template("chat.html")

@app.route("/api/past_chats")
def past_chats():
    url = config["realtime_url"].rstrip("/") + "/conversations.json"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if not data:
                return {"chats": []}
            
            chat_list = []
            for chat_id, messages in data.items():
                chat_list.append({
                    "chat_id": chat_id,
                    "messages": messages
                })
            
            return {"chats": chat_list}
        else:
            return {"chats": []}
    except Exception as e:
        print("Error retrieving chats:", e)
        return {"chats": []}


@app.route("/api/chat", methods=["POST"])
def chat_api():
    init_state()

    user_msg = request.json.get("message", "").strip()
    if user_msg == "":
        return jsonify({"response": "Please type something."})

    # Store user message in session
    session["messages"].append({"role": "user", "content": user_msg})

    step = session["step"]
    details = session["details"]

    if step == "start":
        bot = "It looks like you're interested in a personal loan. Please provide your Customer ID to begin."
        session["step"] = "get_id"

    elif step == "get_id":
        customer_id = user_msg
        details["customer_id"] = customer_id

        verification = verify_customer_details(customer_id)

        if verification:
            details["name"] = verification.get("name")
            bot = f"Hi {details['name']}! I have verified your details. What loan amount are you looking for?"
            session["step"] = "get_amount"
        else:
            bot = "I could not find that Customer ID. Please check and try again."
            session["step"] = "start"

    elif step == "get_amount":
        try:
            loan_amount = int(user_msg)
        except:
            return jsonify({"response": "Please enter a valid numeric loan amount."})

        details["loan_amount"] = loan_amount

        dummy_emi = loan_amount * 0.05
        underwriting = perform_underwriting(details["customer_id"], loan_amount, dummy_emi)

        if "APPROVED" in underwriting:
            generate_sanction_letter_pdf(details["name"], loan_amount, 24)

            bot = (
                f"{underwriting}\n\n"
                "🎉 Your loan has been **APPROVED**!\n"
                "Your sanction letter has been generated and emailed to you."
            )
            session["step"] = "done"
        else:
            bot = f"❌ Your loan was not approved.\nReason: {underwriting}"
            session["step"] = "done"

    else:
        bot = "The loan process is complete. If you need anything else, just ask!"

    # Save bot message
    session["messages"].append({"role": "assistant", "content": bot})
    session.modified = True

    # SAVE conversation to Firebase
    save_chat_to_firebase(user_msg, bot)

    return jsonify({"response": bot})


@app.route("/new_chat")
def new_chat():
    session.clear()         
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
