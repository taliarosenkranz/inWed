import gspread
from google.oauth2.service_account import Credentials
from twilio.rest import Client
import datetime
from flask import Flask, request

# Initialize the Flask app
app = Flask(__name__)

# Twilio setup
account_sid = 'AC3a3e987111747d998af583aec8f29aa4'
auth_token = '5fc9da8410f78a9efccbe2898a48f68c'
client = Client(account_sid, auth_token)

# Google Sheets setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'  # Adding Google Drive access
]
creds = Credentials.from_service_account_file('/Users/talia.rosenkranz/PycharmProjects/inWed/inWed_bot/inwedd-db-9900e29928a2.json', scopes=SCOPES)
client_gspread = gspread.authorize(creds)
sheet = client_gspread.open('inWed_db').sheet1  # Access the first sheet

# Add the root route to avoid 404 for "/"
@app.route("/")
def index():
    return "Welcome to the inWed Bot!"

# Add a placeholder for the favicon to avoid 404 for "/favicon.ico"
@app.route("/favicon.ico")
def favicon():
    return "", 204  # Return a "no content" response

# Send message only via a route or trigger
@app.route("/send-message")
def send_message_route():
    customer_id = '123'
    phone_number = '491637726801'
    send_message_and_log(customer_id, phone_number)
    return "Message sent and logged"

def send_message_and_log(customer_id, phone_number):
    # Send a message with three options
    message_body = """Hello! Please choose one of the following options:
    1. Option A
    2. Option B
    3. Option C

    Reply with the number of your choice."""

    try:
        print(f"Sending WhatsApp message to {phone_number}")
        # Send the WhatsApp message
        message = client.messages.create(
            body=message_body,
            from_='whatsapp:+14155238886',  # Twilio sandbox number
            to=f'whatsapp:+491637726801'
        )

        # Log the message details, including the message SID, in Google Sheets
        print(f"Logging message SID: {message.sid}")
        row_data = [
            customer_id,  # Column 1: Customer ID
            phone_number,  # Column 2: WhatsApp number (phone number)
            message.sid,  # Column 3: Message SID (unique identifier)
            message_body,  # Column 4: Message body text
            '',  # Column 5: Empty, will be filled when the user replies
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Column 6: Timestamp
        ]
        sheet.append_row(row_data)
        #sheet.append_row([customer_id, phone_number, message.sid, message_body, '', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        print(f"Message sent and logged for {phone_number}")

    except Exception as e:
        print(f"Error sending message: {e}")


@app.route("/whatsapp-reply", methods=["POST"])
def whatsapp_reply():
    print(f"Incoming POST request data: {request.form}")

    # Get the incoming message data
    customer_response = request.form.get('Body')
    whatsapp_id = request.form.get('WaId')  # Use WhatsApp ID (WaId) to match
    message_sid = request.form.get('MessageSid')

    print(f"Customer response: {customer_response}, WhatsApp ID: {whatsapp_id}, Message SID: {message_sid}")

    if customer_response and whatsapp_id:
        try:
            # Find the row based on the user's WhatsApp ID (WaId)
            cell = sheet.find(whatsapp_id)  # Search by WaId (WhatsApp ID)
            if cell:
                print(f"Found row: {cell.row} for WhatsApp ID: {whatsapp_id}")
                sheet.update_cell(cell.row, 5, customer_response)  # Update column 5 with the response
                print(f"Response '{customer_response}' logged for WhatsApp ID {whatsapp_id}")
            else:
                print(f"WhatsApp ID {whatsapp_id} not found in Google Sheets.")
        except Exception as e:
            print(f"Error finding or updating the Google Sheet: {e}")
    else:
        print("Error: Missing customer response or WhatsApp ID.")

    return "Reply received and logged",200


# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)