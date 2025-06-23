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

# --- Fictitious Dummy TikTok Data for ZenithFlow Solutions ---
# This list simulates comments/mentions that our connector would fetch from TikTok.
# In a real scenario, this would involve calling the TikTok API.
dummy_tiktok_data = [
    {
        "comment_id": "tiktok_msg_001",
        "video_id": "v101",
        "timestamp": "2025-06-19T12:00:00Z",
        "text": "FlowHub is great for team syncs! Love the new video call integration. #FlowHub #ZenithFlow",
        "user_info": {"id": "tkuser1", "nickname": "CreativeCollab"},
        "comment_url": "https://tiktok.com/video/v101/comment/tk1"
    },
    {
        "comment_id": "tiktok_msg_002",
        "video_id": "v102",
        "timestamp": "2025-06-19T12:30:00Z",
        "text": "@ZenithFlowSupport The FlowHub mobile app is super laggy on my Android device after the last update. Please check! #buggy",
        "user_info": {"id": "tkuser2", "nickname": "TechTrouble"},
        "comment_url": "https://tiktok.com/video/v102/comment/tk2"
    },
    {
        "comment_id": "tiktok_msg_003",
        "video_id": "v103",
        "timestamp": "2025-06-19T13:00:00Z",
        "text": "Wish FlowHub had better integration with Canva for design teams. A direct export feature would be a game-changer! #featureidea",
        "user_info": {"id": "tkuser3", "nickname": "DesignGenius"},
        "comment_url": "https://tiktok.com/video/v103/comment/tk3"
    },
    {
        "comment_id": "tiktok_msg_004",
        "video_id": "v104",
        "timestamp": "2025-06-19T13:15:00Z",
        "text": "Honestly, **Trello** just feels more intuitive than FlowHub sometimes. UI needs work. @ZenithFlowSupport",
        "user_info": {"id": "tkuser4", "nickname": "UIReviewer"},
        "comment_url": "https://tiktok.com/video/v104/comment/tk4"
    }
]

# --- Standardized Normalized Feedback Schema ---
# This schema defines the consistent format for all feedback across sources.
# (This would ideally be imported from a shared utility file in a real project structure)
NORMALIZED_SCHEMA = {
    "message_id": None,          # Unique ID for this piece of feedback across all sources
    "source_platform": None,     # e.g., "twitter", "website", "app_store_ios", "tiktok"
    "timestamp_utc": None,       # When the feedback was created/received (ISO 8601)
    "text_content": None,        # The actual feedback text
    "author_info": {},           # Dictionary for author details (e.g., id, username, email, nickname)
    "original_url": None,        # Link to the original source (if applicable)
    "raw_metadata": {}           # Store the full raw payload for auditing/debugging
}

def process_raw_tiktok_comment_to_normalized_schema(raw_comment):
    """
    Normalizes a raw TikTok comment into the standard schema.
    """
    normalized_feedback = NORMALIZED_SCHEMA.copy()

    try:
        normalized_feedback["message_id"] = f"tiktok-{raw_comment.get('comment_id')}"
        normalized_feedback["source_platform"] = "tiktok"

        timestamp_str = raw_comment.get("timestamp")
        if timestamp_str:
            dt_object = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            normalized_feedback["timestamp_utc"] = dt_object.isoformat(timespec='seconds')

        text_content = raw_comment.get("text", "")
        normalized_feedback["text_content"] = text_content.strip()

        user_data = raw_comment.get("user_info", {})
        normalized_feedback["author_info"] = {
            "id": user_data.get("id"),
            "nickname": user_data.get("nickname") # TikTok specific author info
        }

        normalized_feedback["original_url"] = raw_comment.get("comment_url")
        normalized_feedback["raw_metadata"] = raw_comment

    except Exception as e:
        print(f"ERROR: Failed to process raw TikTok comment ID {raw_comment.get('comment_id', 'N/A')}: {e}")
        return None

    return normalized_feedback

def tiktok_connector_entrypoint(request):
    """
    Cloud Function entry point for the TikTok Connector.
    Triggered on a schedule (e.g., via Cloud Scheduler).
    """
    print(f"TikTok Connector triggered. Project: {PROJECT_ID}, Topic: {RAW_FEEDBACK_TOPIC_NAME}")

    processed_count = 0
    # In a real function, you'd call the TikTok API here.
    for comment in dummy_tiktok_data:
        normalized_data = process_raw_tiktok_comment_to_normalized_schema(comment)
        if normalized_data:
            try:
                data_bytes = json.dumps(normalized_data).encode('utf-8')
                future = publisher.publish(raw_feedback_topic_path, data_bytes)
                message_id = future.result()
                print(f"Published message {message_id} from TikTok (ID: {normalized_data['message_id']}) to raw-feedback-toc.")
                processed_count += 1
            except Exception as e:
                print(f"ERROR: Failed to publish message for TikTok ID {normalized_data.get('message_id', 'N/A')}: {e}")

    print(f"Finished processing {processed_count} dummy TikTok messages.")
    return 'OK', 200
