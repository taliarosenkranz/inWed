import openai
from dotenv import load_dotenv
import os
from flask import Flask, request

# Load environment variables from .env file
load_dotenv()

# Access the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key Loaded: {openai.api_key}")

# Initialize the Flask app
app = Flask(__name__)

# Example function to use OpenAI
def generate_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use your desired OpenAI model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route("/whatsapp-reply", methods=["POST"])
def whatsapp_reply():
    print(f"Incoming POST request data: {request.form}")

    # Get the incoming message data
    customer_response = request.form.get('Body').strip()  # User's message
    whatsapp_id = request.form.get('WaId')  # User's WhatsApp number

    print(f"Customer response: {customer_response}, WhatsApp ID: {whatsapp_id}")

    if customer_response and whatsapp_id:
        try:
            # Pass the user's response to OpenAI's API for processing
            openai_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Use your desired OpenAI model
                messages=[
                    {"role": "system", "content": "You are a helpful wedding RSVP bot."},
                    {"role": "user", "content": customer_response}
                ]
            )

            # Extract the AI-generated reply
            ai_reply = openai_response['choices'][0]['message']['content']

            # Send the AI-generated reply back to the user
            client.messages.create(
                body=ai_reply,
                from_='whatsapp:+[REDACTED_PHONE_NUMBER]',  # Twilio sandbox number
                to=f'whatsapp:+{whatsapp_id}'
            )
            print(f"AI reply sent: {ai_reply}")

        except Exception as e:
            print(f"Error processing OpenAI API: {e}")
    else:
        print("Error: Missing customer response or WhatsApp ID.")

    return "Reply received and logged", 200
