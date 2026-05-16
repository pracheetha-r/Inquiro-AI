import google.generativeai as genai
import os

# We will configure the API key in the main app.py later, 
# but this is how you load it from an environment variable.
# genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def classify_inquiry(name, message, service):
    """
    Takes a client's inquiry details and uses Gemini to categorize it, 
    summarize it, and write a personalized reply.
    """
    
    # 1. Define fallback values in case the AI fails or the network drops.
    # This ensures our app doesn't crash if something goes wrong.
    category = "other"
    summary = "No summary generated."
    reply = "Thank you for reaching out. We will get back to you shortly."
    
    # 2. Build the prompt. This is the exact instruction we send to Gemini.
    # We use f-strings to inject the name, message, and service variables.
    prompt = f"""
    You are an AI assistant for a software agency. 
    A client named '{name}' has sent the following inquiry regarding '{service}':
    "{message}"
    
    Please analyze this inquiry and return exactly three lines of text in the following format. 
    Do not include any other text, markdown, or formatting.
    
    CATEGORY: [Choose exactly one of: web-development, mobile-app, marketing, erp-lms, ai-ml, other]
    SUMMARY: [Write 1-2 sentences describing what the client needs]
    REPLY: [Write a warm 3-4 sentence auto-reply email addressed to {name}]
    """
    
    try:
        # 3. Load the specific Gemini model we want to use.
        # 'gemini-1.5-flash' is fast and cost-effective for these text tasks.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 4. Send the prompt to the model and wait for the response.
        response = model.generate_content(prompt)
        
        # 5. Extract the text from the response and split it into individual lines.
        # .strip() removes extra spaces/newlines at the start and end.
        # .split('\n') breaks the big block of text into a list of separate lines.
        lines = response.text.strip().split('\n')
        
        # 6. Loop through each line to find our required information.
        for line in lines:
            # We use .strip() again to clean up any accidental spaces on the line
            clean_line = line.strip()
            
            # If the line starts with "CATEGORY:", grab everything after it.
            if clean_line.startswith("CATEGORY:"):
                # .replace() removes the "CATEGORY:" label, leaving just the value
                category = clean_line.replace("CATEGORY:", "").strip()
                
            # If the line starts with "SUMMARY:", grab the summary text.
            elif clean_line.startswith("SUMMARY:"):
                summary = clean_line.replace("SUMMARY:", "").strip()
                
            # If the line starts with "REPLY:", grab the email text.
            elif clean_line.startswith("REPLY:"):
                reply = clean_line.replace("REPLY:", "").strip()
                
    except Exception as e:
        # 7. If anything goes wrong (API key error, internet down, etc.), 
        # print the error so we can debug it, and the function will just 
        # return the fallback values we set at the top!
        print(f"Error calling Gemini API: {e}")
        
    # 8. Return all three values back to whoever called this function.
    return category, summary, reply

