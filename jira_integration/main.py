import json
import base64
import os
import requests # Used for making HTTP requests to Jira API (simulated)

# --- Configuration ---
# !!! IMPORTANT: REPLACE WITH YOUR ACTUAL GOOGLE CLOUD PROJECT ID !!!
PROJECT_ID = "YOUR_GOOGLE_CLOUD_PROJECT_ID"
CLASSIFIED_FEEDBACK_TOPIC_NAME = "classified-feedback-topics" # Topic this function consumes from

# --- Jira API Configuration (Conceptual for Dummy Integration) ---
# In a real scenario, these would be actual Jira API details.
# You would get these from your Jira instance's settings.
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://your-zenithflow-jira.atlassian.net") # Fictitious URL
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "your_fictitious_jira_api_token") # Fictitious API Token
JIRA_USER_EMAIL = os.environ.get("JIRA_USER_EMAIL", "jira-bot@zenithflow.com") # Fictitious user email
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "FLOW") # Fictitious Jira Project Key (e.g., "FLOW" for FlowHub)
JIRA_ISSUE_TYPE = os.environ.get("JIRA_ISSUE_TYPE", "Bug") # The issue type to create (e.g., "Bug", "Task")

def create_jira_issue(issue_summary, issue_description, issue_priority="Medium"):
    """
    Simulates creating a Jira issue via API call.
    In a real scenario, this function would make a POST request to Jira's API.
    """
    print(f"SIMULATING JIRA ISSUE CREATION:")
    print(f"  Project: {JIRA_PROJECT_KEY}")
    print(f"  Issue Type: {JIRA_ISSUE_TYPE}")
    print(f"  Summary: {issue_summary}")
    print(f"  Description:\n{issue_description}")
    print(f"  Priority: {issue_priority}")
    print(f"  Jira URL (fictitious): {JIRA_BASE_URL}/browse/{JIRA_PROJECT_KEY}-XYZ") # Placeholder for issue link

    # --- Real Jira API Call (Conceptual) ---
    # headers = {
    #     "Accept": "application/json",
    #     "Content-Type": "application/json"
    # }
    # auth = (JIRA_USER_EMAIL, JIRA_API_TOKEN)
    #
    # payload = json.dumps({
    #     "fields": {
    #         "project": { "key": JIRA_PROJECT_KEY },
    #         "summary": issue_summary,
    #         "description": {
    #             "type": "doc",
    #             "version": 1,
    #             "content": [
    #                 {
    #                     "type": "paragraph",
    #                     "content": [{"type": "text", "text": issue_description}]
    #                 }
    #             ]
    #         },
    #         "issuetype": { "name": JIRA_ISSUE_TYPE },
    #         "priority": { "name": issue_priority } # Map sentiment/category to priority
    #     }
    # })
    #
    # try:
    #     response = requests.post(f"{JIRA_BASE_URL}/rest/api/3/issue", headers=headers, auth=auth, data=payload)
    #     response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
    #     issue_data = response.json()
    #     print(f"  SUCCESS: Simulated Jira Issue Created: {issue_data.get('key')} - {issue_data.get('self')}")
    #     return issue_data.get('key')
    # except requests.exceptions.RequestException as e:
    #     print(f"  ERROR: Simulated Jira API call failed: {e}")
    #     if hasattr(e, 'response') and e.response is not None:
    #         print(f"  Jira API Response: {e.response.text}")
    #     return None
    # --- End Real Jira API Call (Conceptual) ---

    return "SIMULATED_JIRA_KEY_XYZ" # Return a dummy key for simulation

def jira_integration_entrypoint(event, context):
    """
    Cloud Function entry point for Jira Integration.
    Triggered by new messages in the 'classified-feedback-topics' Pub/Sub topic.
    """
    print("Jira Integration Function triggered.")

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

        # --- Check if it's a bug report ---
        if category == "bug_report":
            summary = f"Bug Report from {source_platform}: {text_content[:70]}..."
            description = (
                f"Source: {source_platform}\n"
                f"Message ID: {message_id}\n"
                f"Original Text: {text_content}\n"
                f"Sentiment: {sentiment}\n"
                f"Author: {author_info.get('username', author_info.get('nickname', 'N/A'))} (ID: {author_info.get('id', 'N/A')})\n"
                f"Original URL: {original_url}\n"
                f"\n---\nAutomated by InsightStream AI"
            )

            # Assign priority based on sentiment (e.g., Negative bugs are High priority)
            priority = "Medium"
            if sentiment == "negative":
                priority = "High"

            jira_key = create_jira_issue(summary, description, priority)
            if jira_key:
                print(f"Successfully processed bug report {message_id}. Simulated Jira key: {jira_key}")
            else:
                print(f"Failed to simulate Jira issue creation for {message_id}.")
        elif category == "feature_request":
            print(f"Category is 'feature_request'. Will be handled by Basecamp integration.")
            # This is where Basecamp integration would be triggered
        elif category == "negative_competitor_review":
            print(f"Category is 'negative_competitor_review'. Data stored for review.")
            # This is handled by storage, no immediate action here
        elif sentiment == "positive" and enriched_feedback.get("auto_reply_text"):
            print(f"Category is 'positive' with auto-reply text. Will be handled by Email Reply integration.")
            # This is where Email Reply integration would be triggered
        else:
            print(f"No specific integration action for category '{category}' and sentiment '{sentiment}'. Data is stored.")

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from Pub/Sub message: {e}. Raw data: {message_data_b64}")
        # Consider acknowledging to move past bad messages
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in jira_integration: {e}")
        # Log full traceback for debugging

