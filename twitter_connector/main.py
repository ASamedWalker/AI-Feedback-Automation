import json
import datetime
import uuid
from google.cloud import pubsub_v1

# --- Configuration ---
# !!! IMPORTANT: REPLACE THESE WITH YOUR ACTUAL GOOGLE CLOUD PROJECT ID AND TOPIC NAME !!!
PROJECT_ID = "zenithflow-feedback-automation"
RAW_FEEDBACK_TOPIC_NAME = "raw-feedback-toc" # This is the Pub/Sub topic for all raw, normalized data

publisher = pubsub_v1.PublisherClient()
raw_feedback_topic_path = publisher.topic_path(PROJECT_ID, RAW_FEEDBACK_TOPIC_NAME)

# --- Fictitious Dummy Twitter (X) Data for ZenithFlow Solutions ---
# This list simulates tweets that our connector would fetch from the Twitter (X) API.
# In a real scenario, this would involve calling the Twitter API (e.g., using tweepy or direct HTTP requests).
dummy_twitter_data = [
    {
        "id": "twitter_msg_001",
        "created_at": "2025-06-19T10:00:00Z",
        "text": "FlowHub saved our remote team! Tasks are clearer, communication is smoother. #ZenithFlow",
        "author": {"id": "101", "username": "HappyUser123"},
        "source_url": "https://twitter.com/HappyUser123/status/1"
    },
    {
        "id": "twitter_msg_002",
        "created_at": "2025-06-19T10:15:00Z",
        "text": "Loving FlowHub, but really need a built-in time tracker for tasks! @ZenithFlowSupport #feature_request",
        "author": {"id": "102", "username": "ProductivityGeek"},
        "source_url": "https://twitter.com/ProductivityGeek/status/2"
    },
    {
        "id": "twitter_msg_003",
        "created_at": "2025-06-19T10:30:00Z",
        "text": "Hey @ZenithFlowSupport, FlowHub mobile app is crashing on iOS 17.5 when I try to upload files. #bugreport #FlowHub",
        "author": {"id": "103", "username": "BugHunterPro"},
        "source_url": "https://twitter.com/BugHunterPro/status/3"
    },
    {
        "id": "twitter_msg_004",
        "created_at": "2025-06-19T10:45:00Z",
        "text": "This FlowHub update is a mess. Thinking of switching back to Asana or trying Monday.com again. @ZenithFlowSupport",
        "author": {"id": "104", "username": "FrustratedManager"},
        "source_url": "https://twitter.com/FrustratedManager/status/4"
    },
    {
        "id": "twitter_msg_005",
        "created_at": "2025-06-19T11:00:00Z",
        "text": "Does FlowHub integrate with Google Drive? #FlowHubHelp",
        "author": {"id": "105", "username": "NewbieUser"},
        "source_url": "https://twitter.com/NewbieUser/status/5"
    }
]

# --- Standardized Normalized Feedback Schema ---
# This schema defines the consistent format for all feedback across sources.
# In a larger project, this would be in a shared utility file.
NORMALIZED_SCHEMA = {
    "message_id": None,          # Unique ID for this piece of feedback across all sources
    "source_platform": None,     # e.g., "twitter", "website", "app_store_ios", "tiktok"
    "timestamp_utc": None,       # When the feedback was created/received (ISO 8601)
    "text_content": None,        # The actual feedback text
    "author_info": {},           # Dictionary for author details (e.g., id, username, email, nickname)
    "original_url": None,        # Link to the original source (if applicable)
    "raw_metadata": {}           # Store the full raw payload for auditing/debugging
}

def process_raw_tweet_to_normalized_schema(raw_tweet):
    """
    Normalizes a raw tweet (as if fetched from Twitter API) into the standard schema.
    """
    normalized_feedback = NORMALIZED_SCHEMA.copy()

    try:
        normalized_feedback["message_id"] = f"twitter-{raw_tweet.get('id')}"
        normalized_feedback["source_platform"] = "twitter"

        created_at_str = raw_tweet.get("created_at")
        if created_at_str:
            dt_object = datetime.datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            normalized_feedback["timestamp_utc"] = dt_object.isoformat(timespec='seconds')

        text_content = raw_tweet.get("text", "")
        normalized_feedback["text_content"] = text_content.strip()

        author_data = raw_tweet.get("author", {})
        normalized_feedback["author_info"] = {
            "id": author_data.get("id"),
            "username": author_data.get("username")
        }

        normalized_feedback["original_url"] = raw_tweet.get("source_url")
        normalized_feedback["raw_metadata"] = raw_tweet # Store original raw data

    except Exception as e:
        print(f"ERROR: Failed to process raw tweet ID {raw_tweet.get('id', 'N/A')}: {e}")
        # In a real system, you'd send this error to Google Cloud Logging
        return None

    return normalized_feedback

def twitter_connector_entrypoint(request):
    """
    Cloud Function entry point for the Twitter Connector.
    Triggered on a schedule (e.g., via Cloud Scheduler).
    """
    print(f"Twitter Connector triggered. Project: {PROJECT_ID}, Topic: {RAW_FEEDBACK_TOPIC_NAME}")

    processed_count = 0
    # In a real function, you'd call the Twitter API here to fetch new data.
    # For this dummy setup, we iterate our predefined list.
    for tweet in dummy_twitter_data:
        normalized_data = process_raw_tweet_to_normalized_schema(tweet)
        if normalized_data:
            try:
                # Convert the normalized dictionary to a JSON string, then encode to bytes
                data_bytes = json.dumps(normalized_data).encode('utf-8')

                # Publish the message to Pub/Sub
                future = publisher.publish(raw_feedback_topic_path, data_bytes)
                message_id = future.result() # Blocks until message is published
                print(f"Published message {message_id} from Twitter (ID: {normalized_data['message_id']}) to raw-feedback-toc.")
                processed_count += 1
            except Exception as e:
                print(f"ERROR: Failed to publish message for Twitter ID {normalized_data.get('message_id', 'N/A')}: {e}")
                # Log to Cloud Logging

    print(f"Finished processing {processed_count} dummy Twitter messages.")
    return 'OK', 200  # Return HTTP 200 OK response for Cloud Function success