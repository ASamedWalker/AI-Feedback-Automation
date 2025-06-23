import json
import base64
import os
import pg8000.dbapi # PostgreSQL database driver

# --- Configuration for Database Connection ---
# These values will be set as environment variables in the Cloud Function deployment.
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
DB_PORT = os.environ.get("DB_PORT", "5432") # Default PostgreSQL port

# Expected Enriched Schema (Input from ai_processor)
ENRICHED_SCHEMA_KEYS = [
    "message_id", "source_platform", "timestamp_utc", "text_content",
    "author_info", "original_url", "raw_metadata", "sentiment",
    "category", "detected_competitors", "auto_reply_text", "processing_timestamp_utc"
]

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        raise ValueError("Database connection environment variables are not set.")

    # Using pg8000 for direct connection
    conn = pg8000.dbapi.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=int(DB_PORT)
    )
    return conn

def data_storage_listener_entrypoint(event, context):
    """
    Cloud Function entry point for the Data Storage Listener.
    Triggered by new messages in the 'classified-feedback-topics' Pub/Sub topic.
    """
    print("Data Storage Listener triggered.")

    if not event or not 'data' in event:
        print("No data in Pub/Sub message. Exiting.")
        return

    try:
        # Pub/Sub message data is Base64 encoded
        message_data_b64 = event['data']
        decoded_data_str = base64.b64decode(message_data_b64).decode('utf-8')
        enriched_feedback = json.loads(decoded_data_str)

        print(f"Received classified message for ID: {enriched_feedback.get('message_id')} (Category: {enriched_feedback.get('category')})")

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Prepare data for insertion
            # Convert JSON dicts/lists to JSON strings for insertion into JSONB columns
            author_info_json = json.dumps(enriched_feedback.get("author_info", {}))
            raw_metadata_json = json.dumps(enriched_feedback.get("raw_metadata", {}))
            detected_competitors_json = json.dumps(enriched_feedback.get("detected_competitors", []))

            # SQL INSERT statement with placeholders
            insert_sql = """
            INSERT INTO enriched_feedback (
                message_id, source_platform, timestamp_utc, text_content,
                author_info, original_url, raw_metadata, sentiment,
                category, detected_competitors, auto_reply_text, processing_timestamp_utc
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (message_id) DO UPDATE SET -- Handle potential duplicates gracefully
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
            # Values in the same order as placeholders
            values = (
                enriched_feedback.get("message_id"),
                enriched_feedback.get("source_platform"),
                enriched_feedback.get("timestamp_utc"),
                enriched_feedback.get("text_content"),
                author_info_json, # JSON string
                enriched_feedback.get("original_url"),
                raw_metadata_json, # JSON string
                enriched_feedback.get("sentiment"),
                enriched_feedback.get("category"),
                detected_competitors_json, # JSON string
                enriched_feedback.get("auto_reply_text"),
                enriched_feedback.get("processing_timestamp_utc")
            )

            cursor.execute(insert_sql, values)
            conn.commit()
            print(f"Successfully inserted/updated feedback {enriched_feedback['message_id']} into Cloud SQL.")

        except pg8000.dbapi.Error as db_err:
            if conn:
                conn.rollback() # Rollback in case of error
            print(f"ERROR: Database error during insert for {enriched_feedback.get('message_id')}: {db_err}")
            # Log to Cloud Logging. Consider a dead-letter queue for these messages.
        except Exception as e:
            print(f"ERROR: An unexpected error occurred in data_storage_listener: {e}")
            # Log to Cloud Logging.
        finally:
            if conn:
                conn.close() # Always close the connection

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from Pub/Sub message: {e}. Raw data: {message_data_b64}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred at the start of data_storage_listener: {e}")
