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
    # Send the initial RSVP message to the user
    message_body = """Hello! Will you attend the wedding? Send a reply with 1, 2 or 3.
    1. Yes, I will be coming
    2. No, I will not be coming
    3. I'm not sure yet. Send me another reminder soon"""

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
            message.sid,  # Column 3: Message SID (unique identifier from Twilio)
            message_body,  # Column 4: Message body text
            '',  # Column 5: Empty, to be filled with the user's reply
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Column 6: Timestamp for message sent
            '',  # Column 7: RSVP Status (filled based on reply)
            '',  # Column 8: Guest Count (filled based on reply)
            '',  # Column 9: Arrival Date (filled based on reply)
            '',  # Column 10: Departure Date (filled based on reply)
            '',  # Column 11: Reminder Sent (initially empty)
            ''  # Column 12: Response Timestamp (filled when user replies)
        ]

        # Append the row data to Google Sheets
        sheet.append_row(row_data)

        print(f"Message sent and logged for {phone_number}")

    except Exception as e:
        print(f"Error sending message: {e}")


@app.route("/whatsapp-reply", methods=["POST"])
@app.route("/whatsapp-reply", methods=["POST"])
def whatsapp_reply():
    print(f"Incoming POST request data: {request.form}")

    # Get the incoming message data
    customer_response = request.form.get('Body').strip()  # Get the user's response and trim spaces
    whatsapp_id = request.form.get('WaId')  # Use WhatsApp ID (WaId) to match
    message_sid = request.form.get('MessageSid')

    print(f"Customer response: {customer_response}, WhatsApp ID: {whatsapp_id}, Message SID: {message_sid}")

    if customer_response and whatsapp_id:
        try:
            # Find the row based on the user's WhatsApp ID (WaId)
            cell = sheet.find(whatsapp_id)  # Search by WaId (WhatsApp ID)
            if cell:
                print(f"Found row: {cell.row} for WhatsApp ID: {whatsapp_id}")

                # Retrieve the current conversation step (if any)
                conversation_step = sheet.cell(cell.row, 13).value  # Assuming Column 13 is for "Conversation Step"

                # If no conversation step is logged, assume it's the RSVP step
                if not conversation_step or conversation_step == "RSVP":
                    # Handle the initial RSVP response
                    if customer_response == '1':  # Coming
                        follow_up_message = "Great! Will you come with a +1?\n1: Only me\n2: +1"
                        sheet.update_cell(cell.row, 7, "Coming")  # Update RSVP status in Column 7
                        sheet.update_cell(cell.row, 13, "Guest Count")  # Move to "Guest Count" step
                    elif customer_response == '2':  # Not Coming
                        follow_up_message = "Thank you for letting us know."
                        sheet.update_cell(cell.row, 7, "Not coming")  # Update RSVP status to "Not coming"
                        sheet.update_cell(cell.row, 13, "Completed")  # Mark the conversation as completed
                    elif customer_response == '3':  # Don't know yet
                        follow_up_message = "Thank you, we will remind you again."
                        sheet.update_cell(cell.row, 7, "Undecided")  # Update RSVP status to "Undecided"
                        sheet.update_cell(cell.row, 13, "Completed")  # Mark the conversation as completed
                    else:
                        follow_up_message = "Invalid response. Please reply with 1, 2, or 3."

                # Handle Guest Count response
                elif conversation_step == "Guest Count":
                    if customer_response == '1':  # Only me
                        follow_up_message = "On what date are you planning to arrive? Please answer in DD.MM.YY."
                        sheet.update_cell(cell.row, 8, "1")  # Update Guest Count to "1" in Column 8
                        sheet.update_cell(cell.row, 13, "Arrival Date")  # Move to "Arrival Date" step
                    elif customer_response == '2':  # +1
                        follow_up_message = "On what date are you planning to arrive? Please answer in DD.MM.YY."
                        sheet.update_cell(cell.row, 8, "2")  # Update Guest Count to "2" in Column 8
                        sheet.update_cell(cell.row, 13, "Arrival Date")  # Move to "Arrival Date" step
                    else:
                        follow_up_message = "Invalid response. Please reply with 1 or 2."

                # Handle Arrival Date response
                elif conversation_step == "Arrival Date":
                    # Basic date format validation can be added here
                    follow_up_message = "On what date are you planning to leave? Please answer in DD.MM.YY."
                    sheet.update_cell(cell.row, 9, customer_response)  # Log the arrival date in Column 9
                    sheet.update_cell(cell.row, 13, "Departure Date")  # Move to "Departure Date" step

                # Handle Departure Date response
                elif conversation_step == "Departure Date":
                    # Basic date format validation can be added here
                    follow_up_message = "Great, thank you! We are happy to celebrate with you soon."
                    sheet.update_cell(cell.row, 10, customer_response)  # Log the departure date in Column 10
                    sheet.update_cell(cell.row, 13, "Completed")  # Mark the conversation as completed

                else:
                    follow_up_message = "Invalid response. Please reply with 1, 2, or 3."

                # Send the follow-up message
                client.messages.create(
                    body=follow_up_message,
                    from_='whatsapp:+14155238886',  # Twilio sandbox number
                    to=f'whatsapp:+{whatsapp_id}'
                )
                print(f"Follow-up message sent: {follow_up_message}")

            else:
                print(f"WhatsApp ID {whatsapp_id} not found in Google Sheets.")
        except Exception as e:
            print(f"Error finding or updating the Google Sheet: {e}")
    else:
        print("Error: Missing customer response or WhatsApp ID.")

    return "Reply received and logged", 200




# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
