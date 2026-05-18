import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types
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
gemini_client = None
if gemini_api_key and gemini_api_key != "your_gemini_api_key":
    gemini_client = genai.Client(api_key=gemini_api_key)

# Initialize Resend client for sending emails
resend.api_key = os.getenv("RESEND_API_KEY", "")

def classify_inquiry(name, message, service):
    """
    Takes a client's inquiry details and uses Gemini to categorize it, 
    summarize it, and write a personalized reply.
    """
    
    # 1. Define clean fallback values in case the AI fails.
    category = "General"
    summary = "A new inquiry has been submitted by the client."
    reply = (
        f"Dear {name},\n\n"
        "Thank you for reaching out to us.\n\n"
        "We have received your inquiry successfully. One of our executives will review your requirements and get in touch with you shortly to assist you further.\n\n"
        "Best regards,\n"
        "Team Inquiro AI"
    )
    
    if not gemini_api_key or gemini_api_key == "your_gemini_api_key":
        return category, "AI Summary disabled (API key missing).", reply
        
    # 2. Build the prompt.
    prompt = f"""
    You are an expert AI assistant for a software agency.
    A client named '{name}' has sent the following inquiry regarding '{service}':
    "{message}"

    Analyze this inquiry and return ONLY valid JSON with exactly this schema. Do not include markdown code blocks.
    {{
      "category": "Choose exactly one of: Web Development, Mobile App, Marketing, SEO, AI/ML, ERP/LMS, General",
      "summary": "Write a professional 1-sentence summary of what the client wants. Do not just copy their message.",
      "reply": "Write a professional, warm, and personalized 3-4 sentence auto-reply email addressed to {name}, directly addressing their specific request."
    }}
    """
    
    try:
        # Enforce JSON output so Gemini doesn't add conversational text
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        response_text = response.text.strip()
        print("Raw Gemini Response:", response_text) # Helpful for debugging in the terminal

        # Clean markdown if present just in case
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text, flags=re.DOTALL).strip()

        # Parse JSON
        parsed = json.loads(response_text)
        
        # Extract values
        if parsed.get("category"):
            category = parsed["category"].strip()
        if parsed.get("summary"):
            summary = parsed["summary"].strip()
        if parsed.get("reply"):
            reply = parsed["reply"].strip()
            
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        # If Gemini fails, it will safely return the clean fallback values defined at the top
        
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
