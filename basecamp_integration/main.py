import json
import base64
import os
import requests # Could be used for Basecamp API calls in real scenario

# --- Configuration ---
# !!! IMPORTANT: REPLACE WITH YOUR ACTUAL GOOGLE CLOUD PROJECT ID !!!
PROJECT_ID = "zenithflow-feedback-automation"
CLASSIFIED_FEEDBACK_TOPIC_NAME = "classified-feedback-topics" # Topic this function consumes from

# --- Basecamp API Configuration (Conceptual for Dummy Integration) ---
# In a real scenario, these would be actual Basecamp API details.
# You would get these from your Basecamp account.
BASECAMP_ACCESS_TOKEN = os.environ.get("BASECAMP_ACCESS_TOKEN", "your_fictitious_basecamp_token")
BASECAMP_ACCOUNT_ID = os.environ.get("BASECAMP_ACCOUNT_ID", "1234567") # Fictitious Basecamp Account ID
BASECAMP_PROJECT_ID = os.environ.get("BASECAMP_PROJECT_ID", "7890123") # Fictitious Basecamp Project ID
BASECAMP_TODOSET_ID = os.environ.get("BASECAMP_TODOSET_ID", "456789") # Fictitious Basecamp To-do list ID

def create_basecamp_todo(todo_title, todo_description):
    """
    Simulates creating a to-do item in Basecamp via API call.
    In a real scenario, this function would make a POST request to Basecamp's API.
    """
    print(f"SIMULATING BASECAMP TO-DO CREATION:")
    print(f"  Account ID: {BASECAMP_ACCOUNT_ID}")
    print(f"  Project ID: {BASECAMP_PROJECT_ID}")
    print(f"  To-do Title: {todo_title}")
    print(f"  To-do Description:\n{todo_description}")

    # --- Real Basecamp API Call (Conceptual) ---
    # headers = {
    #     "Content-Type": "application/json",
    #     "Authorization": f"Bearer {BASECAMP_ACCESS_TOKEN}",
    #     "User-Agent": "InsightStream AI (your-email@example.com)" # Required by Basecamp API
    # }
    #
    # payload = json.dumps({
    #     "content": todo_title,
    #     "description": todo_description
    # })
    #
    # try:
    #     # Example for creating a to-do in a specific to-do list (TodoSet)
    #     response = requests.post(
    #         f"https://basecamp.com/{BASECAMP_ACCOUNT_ID}/api/v1/projects/{BASECAMP_PROJECT_ID}/todosets/{BASECAMP_TODOSET_ID}/todos.json",
    #         headers=headers,
    #         data=payload
    #     )
    #     response.raise_for_status()
    #     todo_data = response.json()
    #     print(f"  SUCCESS: Simulated Basecamp To-do Created: {todo_data.get('id')} - {todo_data.get('url')}")
    #     return todo_data.get('id')
    # except requests.exceptions.RequestException as e:
    #     print(f"  ERROR: Simulated Basecamp API call failed: {e}")
    #     if hasattr(e, 'response') and e.response is not None:
    #         print(f"  Basecamp API Response: {e.response.text}")
    #     return None
    # --- End Real Basecamp API Call (Conceptual) ---

    return "SIMULATED_BASECAMP_TODO_ID_XYZ" # Return a dummy ID for simulation

def basecamp_integration_entrypoint(event, context):
    """
    Cloud Function entry point for Basecamp Integration.
    Triggered by new messages in the 'classified-feedback-topics' Pub/Sub topic.
    """
    print("Basecamp Integration Function triggered.")

    if not event or not 'data' in event:
        print("No data in Pub/Sub message. Exiting.")
        return

    try:
        message_data_b64 = event['data']
        decoded_data_str = base64.b64decode(message_data_b64).decode('utf-8')
        enriched_feedback = json.loads(decoded_data_str)

        message_id = enriched_feedback.get('message_id')
        category = enriched_feedback.get('category')
        text_content = enriched_feedback.get('text_content')
        source_platform = enriched_feedback.get('source_platform')
        sentiment = enriched_feedback.get('sentiment')
        original_url = enriched_feedback.get('original_url', 'N/A')
        author_info = enriched_feedback.get('author_info', {})

        print(f"Processing message ID: {message_id} (Category: {category})")

        # --- Check if it's a feature request ---
        if category == "feature_request":
            title = f"Feature Request from {source_platform}: {text_content[:70]}..."
            description = (
                f"Source: {source_platform}\n"
                f"Message ID: {message_id}\n"
                f"Original Text: {text_content}\n"
                f"Sentiment: {sentiment}\n"
                f"Author: {author_info.get('username', author_info.get('nickname', 'N/A'))} (ID: {author_info.get('id', 'N/A')})\n"
                f"Original URL: {original_url}\n"
                f"\n---\nAutomated by InsightStream AI"
            )

            basecamp_id = create_basecamp_todo(title, description)
            if basecamp_id:
                print(f"Successfully processed feature request {message_id}. Simulated Basecamp To-do ID: {basecamp_id}")
            else:
                print(f"Failed to simulate Basecamp To-do creation for {message_id}.")
        else:
            print(f"No Basecamp action for category '{category}'. Data is stored and other integrations handled.")

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from Pub/Sub message: {e}. Raw data: {message_data_b64}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in basecamp_integration: {e}")
