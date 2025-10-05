from flask import Flask, request
import pandas as pd
import requests
import json
from twilio.rest import Client
import fitz  # PyMuPDF for PDF text extraction
from io import BytesIO

# ---- Load CSV and Get Unique Subjects ----
try:
    data = pd.read_csv("rag-link - AIML.csv")
    UNIQUE_SUBJECTS = data['subject'].unique().tolist()
    print("--- Found Unique Subjects ---")
    print(UNIQUE_SUBJECTS)
    print("---------------------------")
except FileNotFoundError:
    print("Error: 'rag-link - AIML.csv' not found. Please make sure the file is in the same directory.")
    exit()

# ---- Configure OpenRouter ----
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ---- Configure Twilio ----
ACCOUNT_SID = "SKaaf9a6b4696c310e86f25ec7620fbf1b"
AUTH_TOKEN = "JVgJV7j5IeUrilnC40VeP3RKUH61MxnY"
FROM_NUMBER = "whatsapp:+14155238886"

client = Client(ACCOUNT_SID, AUTH_TOKEN)
app = Flask(__name__)

# ---- Memory for user context ----
user_context = {}

# ---- Helper: Extract text from PDF ----
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

# ---- Helper: Ask OpenRouter model about a PDF ----
def ask_llm_about_pdf(text, question):
    try:
        system_prompt = (
            "You are an expert tutor answering questions based only on the provided study notes. "
            "Use the given text strictly to answer the question briefly and clearly, suitable for exams."
        )
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "anthropic/claude-3-haiku",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Notes:\n{text}\n\nQuestion: {question}"}
            ],
            "max_tokens": 400
        }
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error in ask_llm_about_pdf: {e}")
        return "⚠️ Sorry, I couldn’t process that question right now."

# ---- Helper: Append options to every reply ----
def append_options(reply):
    return reply + "\n\n👉 What would you like to do next?\n1️⃣ Ask questions about this note\n2️⃣ Continue retrieving"

# ---- OpenRouter Function for subject extraction ----
def extract_query_details(message, subject_list):
    subject_options = ", ".join(f"'{s}'" for s in subject_list)
    system_prompt = (
        f"You are an expert at information retrieval. Your job is to extract specific details from a user's request. "
        f"The available full subject names are: [{subject_options}]. "
        f"You must extract the following fields if they are mentioned: 'faculty', 'subject', 'subject_code', 'semester', 'module'.\n"
        f"- For the 'subject' key, you MUST map user abbreviations to one of the full subject names from the list. (e.g., 'ai' -> 'ARTIFICIAL INTELLIGENCE').\n"
        f"- For the 'subject_code' key, look for alphanumeric codes (e.g., 'BCS515C', 'BAD402').\n"
        f"Return a valid JSON object with five keys: 'faculty', 'subject', 'subject_code', 'semester', 'module'. "
        f"If a detail is not found, its value should be an empty string. For 'semester' and 'module', 'all' is also acceptable."
    )
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
        "max_tokens": 200,
        "response_format": {"type": "json_object"}
    }
    default_response = {"faculty": "", "subject": "", "subject_code": "", "semester": "all", "module": "all"}
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        json_content = response.json()["choices"][0]["message"]["content"]
        return json.loads(json_content)
    except Exception as e:
        print(f"Error in extract_query_details: {e}")
        return default_response

# ---- WhatsApp Message Handler ----
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    print(f"\n📩 Message from {from_number}: '{incoming_msg}'")

    if from_number in user_context:
        ctx = user_context[from_number]
        if ctx["mode"] == "awaiting_choice":
            if incoming_msg == "1":
                ctx["mode"] = "qa"
                reply = "🧠 You can now ask questions about the notes I found!"
                client.messages.create(from_=FROM_NUMBER, body=reply, to=from_number)
                return "OK", 200
            elif incoming_msg == "2":
                del user_context[from_number]
                reply = "✅ You can now continue retrieving resources."
                client.messages.create(from_=FROM_NUMBER, body=reply, to=from_number)
                return "OK", 200

        elif ctx["mode"] == "qa":
            pdf_paths = ctx.get("pdf_paths", [])
            combined_text = ""
            if not pdf_paths:
                 answer = "I seem to have lost the notes. Please try searching again."
            else:
                for path in pdf_paths:
                    print(f"   ...reading {path}")
                    combined_text += extract_text_from_pdf(path) + "\n\n"
                answer = ask_llm_about_pdf(combined_text, incoming_msg)
            reply = append_options(answer)
            client.messages.create(from_=FROM_NUMBER, body=reply, to=from_number)
            return "OK", 200

    processed_msg = incoming_msg.lower()
    ordinal_map = {"first": "1", "1st": "1", "second": "2", "2nd": "2", "third": "3", "3rd": "3", "fourth": "4", "4th": "4", "fifth": "5", "5th": "5", "sixth": "6", "6th": "6"}
    for word, digit in ordinal_map.items():
        processed_msg = processed_msg.replace(word, digit)
    print(f"🔍 Processed query: '{processed_msg}'")

    try:
        details = extract_query_details(processed_msg, UNIQUE_SUBJECTS)
        print(f"🧩 Extracted details: {details}")

        # ---- NEW: Handle generic greetings before attempting a search ----
        is_search_query = any([details.get("faculty"), details.get("subject"), details.get("subject_code")])
        if not is_search_query:
            # If no primary search terms were found, send a welcome message and stop.
            reply = (
                "👋 Hello! I'm here to help you find study resources.\n\n"
                "Please tell me what you're looking for. You can search by subject, subject code, faculty, module, or semester.\n\n"
                "*For example:*\n"
                "• `AI notes module 3`\n"
                "• `notes for BCS515C`"
            )
            client.messages.create(from_=FROM_NUMBER, body=reply, to=from_number)
            return "OK", 200
        # ---- END OF NEW SECTION ----


        query_result = data.copy() # Start with all data

        # Sequentially apply filters for each detail found
        if details.get("faculty"):
            query_result = query_result[query_result["faculty"].str.contains(details["faculty"], case=False, na=False)]
        
        if details.get("subject"):
            query_result = query_result[query_result["subject"].str.lower() == details["subject"].lower()]
            
        if details.get("subject_code"):
            query_result = query_result[query_result["subject-code"].str.lower() == details["subject_code"].lower()]
            
        if details.get("semester") and str(details["semester"]).lower() != 'all':
            query_result = query_result[query_result['semester'].astype(str) == str(details["semester"])]
            
        if details.get("module") and str(details["module"]).lower() != 'all':
            query_result = query_result[query_result['module'].astype(str) == str(details["module"])]

        if not query_result.empty:
            links = "\n".join(query_result["resource-link"].tolist())
            reply = f"📘 Found {len(query_result)} resource(s):\n{links}"
            file_ids = query_result["id"].astype(str).tolist()
            pdf_paths = [f"downloads/{file_id}.pdf" for file_id in file_ids]
            user_context[from_number] = {"mode": "awaiting_choice", "pdf_paths": pdf_paths}
            reply = append_options(reply)
        else:
            reply = "❌ Sorry, no matching resources found. Please refine your query."

    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        reply = "⚠️ An error occurred while processing your request. Please try again."

    print(f"📤 Sending reply: {reply}")
    client.messages.create(from_=FROM_NUMBER, body=reply, to=from_number)
    return "OK", 200

# ---- Main execution ----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)