import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import resend

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for Next.js app
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")
supabase: Client | None = None
if supabase_url and supabase_key and supabase_url != "your_supabase_url":
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Error initializing Supabase: {e}")

# Initialize Gemini client
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if gemini_api_key and gemini_api_key != "your_gemini_api_key":
    genai.configure(api_key=gemini_api_key)

# Initialize Resend client for sending emails
resend.api_key = os.getenv("RESEND_API_KEY", "")

def build_fallback_summary(message, service):
    clean_message = " ".join((message or "").split()).strip()
    service_text = (service or "").strip()

    if clean_message:
        snippet = clean_message[:180]
        if len(clean_message) > 180:
            snippet += "..."
        if service_text:
            return f"Client requested help with {service_text}. {snippet}"
        return f"Client inquiry: {snippet}"

    if service_text:
        return f"Client requested help with {service_text}."
    return "Client submitted an inquiry."

def normalize_domain_keyword(value):
    raw = (value or "").strip()
    if not raw:
        return "General"

    normalized = re.sub(r"\s+", " ", raw.replace("_", " ").replace("-", " ")).strip()
    lowered = normalized.lower()

    if lowered == "ai ml":
        return "AI/ML"
    if lowered == "erp lms":
        return "ERP/LMS"

    return normalized.title() if normalized else "General"

def build_short_summary_sentence(summary_text, message):
    source = (summary_text or "").strip()

    if source:
        source = re.sub(r"^[A-Za-z][A-Za-z0-9/& \-]{1,40}:\s*", "", source).strip()

    if not source:
        source = " ".join((message or "").split()).strip()
    if not source:
        source = "Client needs assistance."

    source = re.sub(r"\s+", " ", source).strip().rstrip(".!?")
    source = re.sub(
        r"^(?:the client|client)\s+(?:is\s+)?(?:seeking|looking for|needs|wants|requires|requested)\s+",
        "",
        source,
        flags=re.IGNORECASE,
    )
    source = re.sub(
        r"^(?:we|i|our team|our company|my team|my company)\s+(?:are\s+)?(?:looking for|seeking|need|want|require)\s+",
        "",
        source,
        flags=re.IGNORECASE,
    )
    source = re.sub(
        r"^(?:need|needs|want|wants|require|requires|looking for|seeking)\s+",
        "",
        source,
        flags=re.IGNORECASE,
    )

    first_sentence = re.split(r"(?<=[.!?])\s+", source, maxsplit=1)[0].strip().rstrip(".!?")
    if len(first_sentence) > 130:
        first_sentence = first_sentence[:127].rstrip() + "..."
    if not first_sentence:
        first_sentence = "assistance with their requirement"

    if first_sentence.endswith("..."):
        return f"The client is seeking {first_sentence}"
    return f"The client is seeking {first_sentence}."

def build_domain_summary(category, service, summary_text, message):
    domain_source = (service or "").strip() or (category or "").strip() or "General"
    domain_keyword = normalize_domain_keyword(domain_source)
    short_sentence = build_short_summary_sentence(summary_text, message)
    return f"{domain_keyword}: {short_sentence}"

def build_default_reply(name):
    client_name = (name or "").strip() or "Client"
    return (
        f"Dear {client_name},\n\n"
        "Thank you for reaching out to us.\n\n"
        "We have received your inquiry successfully. One of our executives will review your requirements and get in touch with you shortly to assist you further.\n\n"
        "We appreciate your interest and look forward to connecting with you.\n\n"
        "Best regards,\n"
        "Team Inquiro AI"
    )

def classify_inquiry(name, message, service):
    """
    Takes a client's inquiry details and uses Gemini to categorize it, 
    summarize it, and write a personalized reply.
    """
    
    # 1. Define fallback values in case the AI fails or the network drops.
    category = "General"
    summary = build_domain_summary(category, service, "", message)
    reply = build_default_reply(name)
    
    if not gemini_api_key or gemini_api_key == "your_gemini_api_key":
        return category, summary, reply
        
    # 2. Build the prompt. This is the exact instruction we send to Gemini.
    prompt = f"""
    You are an AI assistant for a software agency.
    A client named '{name}' has sent the following inquiry regarding '{service}':
    "{message}"

    Analyze this inquiry and return ONLY valid JSON with this schema:
    {{
      "category": "Choose exactly one of: web-development, mobile-app, marketing, erp-lms, ai-ml, General",
      "summary": "One short sentence in indirect voice (third person), easy to grasp, describing what the client needs",
      "reply": "A warm 3-4 sentence auto-reply email addressed to {name}"
    }}
    """
    
    try:
        # 3. Load the specific Gemini model we want to use.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 4. Send the prompt to the model and wait for the response.
        response = model.generate_content(prompt)
        
        response_text = ""
        try:
            response_text = (response.text or "").strip()
        except Exception:
            response_text = ""

        if not response_text:
            extracted_parts = []
            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if not content:
                    continue
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        extracted_parts.append(part_text)
            response_text = "\n".join(extracted_parts).strip()

        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text, flags=re.DOTALL).strip()

        parsed = None
        try:
            parsed = json.loads(response_text)
        except Exception:
            parsed = None

        if isinstance(parsed, dict):
            category = str(parsed.get("category", category)).strip() or category
            summary = str(parsed.get("summary", summary)).strip() or summary
            reply = str(parsed.get("reply", reply)).strip() or reply
        else:
            # Fallback for non-JSON responses
            lines = response_text.split('\n')
            for line in lines:
                clean_line = line.strip()
                normalized = clean_line.replace("**", "")
                if normalized.upper().startswith("CATEGORY:"):
                    category = normalized.split(":", 1)[1].strip() or category
                elif normalized.upper().startswith("SUMMARY:"):
                    summary = normalized.split(":", 1)[1].strip() or summary
                elif normalized.upper().startswith("REPLY:"):
                    reply = normalized.split(":", 1)[1].strip() or reply

        summary = build_domain_summary(category, service, summary, message)
        if not reply.strip():
            reply = build_default_reply(name)
                
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        summary = build_domain_summary(category, service, "", message)
        reply = build_default_reply(name)
        
    # 8. Return all three values back to whoever called this function.
    return category, summary, reply


@app.route("/api/inquiry", methods=["POST"])
def create_inquiry():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    name = data.get("name")
    email = data.get("email")
    company = data.get("company", "")
    message = data.get("message")
    service = data.get("service", "")
    
    if not name or not email or not message:
        return jsonify({"error": "Name, email, and message are required"}), 400
        
    # Generate AI Category, Summary, and Reply using Gemini
    ai_category, ai_summary, ai_reply = classify_inquiry(name, message, service)
    
    inquiry_data = {
        "name": name,
        "email": email,
        "company": company,
        "message": message,
        "service": service,
        "ai_category": ai_category,
        "ai_summary": ai_summary
    }
    
    # Save to Supabase
    if supabase:
        try:
            response = supabase.table("inquiries").insert(inquiry_data).execute()
            saved_data = response.data[0] if hasattr(response, 'data') and response.data else inquiry_data
            
            # --- NEW: SEND EMAIL VIA RESEND ---
            # If the Resend API key is set, attempt to send the AI reply as an email!
            if resend.api_key and resend.api_key != "your_resend_api_key":
                try:
                    resend.Emails.send({
                        # 'onboarding@resend.dev' is a testing email provided by Resend. 
                        # In production, you would use your own verified domain (e.g., hello@yourcompany.com)
                        "from": "Inquiro AI <onboarding@resend.dev>",
                        "to": email,  # Sending to the client's email address
                        "subject": "Thank you for your inquiry!",
                        "text": ai_reply  # The personalized reply generated by Gemini
                    })
                    print(f"Successfully sent reply email to {email}")
                except Exception as e:
                    print(f"Error sending email via Resend: {e}")
            # ----------------------------------
            
            # We also return the generated AI reply back to the frontend, even if not stored in DB yet
            return jsonify({
                "message": "Inquiry created successfully", 
                "data": saved_data,
                "ai_reply": ai_reply
            }), 201
        except Exception as e:
            print(f"Supabase insertion error: {e}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    else:
        # Fallback if Supabase is not configured
        print("Warning: Supabase not configured. Data not saved.")
        return jsonify({
            "message": "Inquiry processed (but not saved, DB missing)", 
            "data": inquiry_data,
            "ai_reply": ai_reply
        }), 201

@app.route("/api/inquiries", methods=["GET"])
def get_inquiries():
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500
        
    try:
        # Fetch all inquiries ordered by newest first
        response = supabase.table("inquiries").select("*").order("created_at", desc=True).execute()
        
        # Format the response to handle datetime objects correctly if needed
        data = response.data if hasattr(response, 'data') else []
        return jsonify(data), 200
    except Exception as e:
        print(f"Supabase fetch error: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
