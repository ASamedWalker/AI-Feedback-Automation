import json
import base64
import os
import requests # Could be used for SendGrid/Mailgun API calls in real scenario

# --- Configuration ---
# !!! IMPORTANT: REPLACE WITH YOUR ACTUAL GOOGLE CLOUD PROJECT ID !!!
PROJECT_ID = "zenithflow-feedback-automation"
CLASSIFIED_FEEDBACK_TOPIC_NAME = "classified-feedback-topics" # Topic this function consumes from

# --- Email Service Configuration (Conceptual for Dummy Integration) ---
# In a real scenario, these would be actual SendGrid/Mailgun API details.
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "your_fictitious_sendgrid_api_key")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "support@zenithflow.com") # Fictitious sender email

def send_simulated_email(to_email, subject, body):
    """
    Simulates sending an email using a transactional email service API (like SendGrid).
    In a real scenario, this would make an HTTP POST request to the email service API.
    """
    print(f"SIMULATING EMAIL SEND:")
    print(f"  To: {to_email}")
    print(f"  From: {SENDER_EMAIL}")
    print(f"  Subject: {subject}")
    print(f"  Body:\n{body}")

    # --- Real Email Service API Call (Conceptual) ---
    # Example for SendGrid (install 'sendgrid' library and uncomment):
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    #
    # message = Mail(
    #     from_email=SENDER_EMAIL,
    #     to_emails=to_email,
    #     subject=subject,
    #     html_content=body)
    # try:
    #     sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
    #     response = sendgrid_client.send(message)
    #     print(f"  SUCCESS: Simulated Email sent. Status Code: {response.status_code}")
    #     return True
    # except Exception as e:
    #     print(f"  ERROR: Simulated Email API call failed: {e}")
    #     return False
    # --- End Real Email Service API Call (Conceptual) ---

    return True # Return True for simulation success

def email_reply_integration_entrypoint(event, context):
    """
    Cloud Function entry point for Email Reply Integration.
    Triggered by new messages in the 'classified-feedback-topics' Pub/Sub topic.
    """
    print("Email Reply Integration Function triggered.")

    if not event or not 'data' in event:
        print("No data in Pub/Sub message. Exiting.")
        return

    try:
        message_data_b64 = event['data']
        decoded_data_str = base64.b64decode(message_data_b64).decode('utf-8')
        enriched_feedback = json.loads(decoded_data_str)

        message_id = enriched_feedback.get('message_id')
        category = enriched_feedback.get('category')
        sentiment = enriched_feedback.get('sentiment')
        auto_reply_text = enriched_feedback.get('auto_reply_text')
        original_text = enriched_feedback.get('text_content')
        source_platform = enriched_feedback.get('source_platform')
        author_info = enriched_feedback.get('author_info', {})

        print(f"Processing message ID: {message_id} (Category: {category}, Sentiment: {sentiment})")

        # --- Check if it's positive feedback with an auto-reply ---
        # We assume auto_reply_text is present for positive feedback,
        # but also check category to avoid replying to positive bug reports if desired.
        if sentiment == "positive" and auto_reply_text and category != "bug_report":
            # For dummy data, we don't have real customer emails, so we'll use a placeholder.
            # In a real system, you'd extract 'to_email' from 'author_info' or 'raw_metadata'.
            to_email = f"customer_{author_info.get('username', 'anonymous')}@example.com" # Fictitious customer email

            subject = f"Thank You for your Feedback on FlowHub! (Ref: {message_id})"
            body = auto_reply_text # The AI-generated reply

            if send_simulated_email(to_email, subject, body):
                print(f"Successfully simulated sending auto-reply for message {message_id}.")
            else:
                print(f"Failed to simulate sending auto-reply for message {message_id}.")
        else:
            print(f"No auto-reply action for message ID {message_id} (Category: {category}, Sentiment: {sentiment}).")

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from Pub/Sub message: {e}. Raw data: {message_data_b64}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in email_reply_integration: {e}")

