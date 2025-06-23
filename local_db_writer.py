import json
import os
import pg8000.dbapi
from google.cloud import pubsub_v1

# --- Configuration ---
# !!! IMPORTANT: REPLACE THESE WITH YOUR ACTUAL VALUES !!!
PROJECT_ID = "zenithflow-feedback-automation"
CLASSIFIED_FEEDBACK_TOPIC_NAME = "classified-feedback-topics"

# --- Cloud SQL Database Configuration ---
# These are your Cloud SQL instance's Public IP, user, password, etc.
# Make sure your local machine's IP is authorized in Cloud SQL!
DB_HOST = "34.121.72.3" # <--- REPLACE WITH YOUR CLOUD SQL PUBLIC IP
DB_USER = "feedback_user"
DB_PASSWORD = "123" # <--- REPLACE WITH YOUR DB USER PASSWORD
DB_NAME = "feedback_db"
DB_PORT = "5432"

# Pub/Sub subscriber client
subscriber = pubsub_v1.SubscriberClient()
# Create a subscription for this local script to listen to.
# This creates a NEW subscription, don't reuse the one for the data_storage_listener CF.
SUBSCRIPTION_PATH = subscriber.subscription_path(PROJECT_ID, "local-db-writer-subscription")

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = pg8000.dbapi.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=int(DB_PORT)
        )
        return conn
    except Exception as e:
        print(f"ERROR: Could not establish database connection: {e}")
        raise # Re-raise to stop execution if connection fails

# --- Data Insertion Logic (Copied from data_storage_listener) ---
def insert_enriched_feedback(conn, enriched_feedback):
    """Inserts a single enriched feedback message into the database."""
    cursor = conn.cursor()

    author_info_json = json.dumps(enriched_feedback.get("author_info", {}))
    raw_metadata_json = json.dumps(enriched_feedback.get("raw_metadata", {}))
    detected_competitors_json = json.dumps(enriched_feedback.get("detected_competitors", []))

    insert_sql = """
    INSERT INTO enriched_feedback (
        message_id, source_platform, timestamp_utc, text_content,
        author_info, original_url, raw_metadata, sentiment,
        category, detected_competitors, auto_reply_text, processing_timestamp_utc
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) ON CONFLICT (message_id) DO UPDATE SET
        source_platform = EXCLUDED.source_platform,
        timestamp_utc = EXCLUDED.timestamp_utc,
        text_content = EXCLUDED.text_content,
        author_info = EXCLUDED.author_info,
        original_url = EXCLUDED.original_url,
        raw_metadata = EXCLUDED.raw_metadata,
        sentiment = EXCLUDED.sentiment,
        category = EXCLUDED.category,
        detected_competitors = EXCLUDED.detected_competitors,
        auto_reply_text = EXCLUDED.auto_reply_text,
        processing_timestamp_utc = EXCLUDED.processing_timestamp_utc;
    """
    values = (
        enriched_feedback.get("message_id"),
        enriched_feedback.get("source_platform"),
        enriched_feedback.get("timestamp_utc"),
        enriched_feedback.get("text_content"),
        author_info_json,
        enriched_feedback.get("original_url"),
        raw_metadata_json,
        enriched_feedback.get("sentiment"),
        enriched_feedback.get("category"),
        detected_competitors_json,
        enriched_feedback.get("auto_reply_text"),
        enriched_feedback.get("processing_timestamp_utc")
    )

    cursor.execute(insert_sql, values)
    conn.commit()
    print(f"Successfully inserted/updated feedback {enriched_feedback['message_id']} into Cloud SQL.")


# --- Main Listener Logic ---
def callback(message: pubsub_v1.subscriber.message.Message):
    """Callback function for processing Pub/Sub messages."""
    print(f"Received message: {message.message_id}")
    try:
        enriched_feedback = json.loads(message.data.decode('utf-8'))
        print(f"Processing classified message for ID: {enriched_feedback.get('message_id')} (Category: {enriched_feedback.get('category')})")

        conn = None
        try:
            conn = get_db_connection()
            insert_enriched_feedback(conn, enriched_feedback)
            message.ack() # Acknowledge the message if successfully processed
            print(f"Message {message.message_id} acknowledged.")
        except Exception as db_err:
            print(f"ERROR: Failed to write to DB for message {message.message_id}: {db_err}")
            message.nack() # Negatively acknowledge if processing fails, so it can be retried
            if conn: conn.rollback()
        finally:
            if conn: conn.close()

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from Pub/Sub message {message.message_id}: {e}")
        message.ack() # Acknowledge bad messages to avoid reprocessing
    except Exception as e:
        print(f"ERROR: Unhandled error for message {message.message_id}: {e}")
        message.nack()

if __name__ == "__main__":
    print(f"Listening for messages on {SUBSCRIPTION_PATH}...")
    # The subscriber client is an asynchronous context manager.
    # It starts a thread to pull messages.
    streaming_pull_future = subscriber.subscribe(SUBSCRIPTION_PATH, callback=callback)
    print("Listening... Press Ctrl+C to exit.")

    # Wrap the subscribe call in a try/finally block to ensure resources are properly cleaned up.
    try:
        # Blocks the main thread to keep the script running and listening
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel() # Triggers the shutdown
        streaming_pull_future.result() # Wait for the shutdown to complete
    finally:
        subscriber.api.transport.close() # Close the Pub/Sub transport
        print("Stopped listening.")
