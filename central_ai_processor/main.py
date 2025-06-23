import json
import base64
import random # For simulating AI output
import datetime
from google.cloud import language_v1 # For actual NLP calls
from google.cloud import pubsub_v1 # For publishing classified data
import re # For competitor detection (simple regex for demo)
# For Vertex AI/GEMINI API calls
from vertexai.preview.generative_models import GenerativeModel, Part

# --- Configuration ---
# !!! IMPORTANT: REPLACE THESE WITH YOUR ACTUAL GOOGLE CLOUD PROJECT ID AND TOPIC NAMES !!!
PROJECT_ID = "zenithflow-feedback-automation"
RAW_FEEDBACK_TOPIC_NAME = "raw-feedback-toc" # Topic this function consumes from
CLASSIFIED_FEEDBACK_TOPIC_NAME = "classified-feedback-topics" # Topic this function publishes to
REGION = "us-central1" # Your Google Cloud region

# Pub/Sub client for publishing classified data
publisher = pubsub_v1.PublisherClient()
classified_feedback_topic_path = publisher.topic_path(PROJECT_ID, CLASSIFIED_FEEDBACK_TOPIC_NAME)

# Google Cloud Natural Language API client (for real NLP)
nlp_client = language_v1.LanguageServiceClient()


# Vertex AI / Gemini API client
# Use 'gemini-pro' for text generation
gemini_model = GenerativeModel("gemini-2.5-pro")

# --- Standardized Normalized Feedback Schema (Expected Input) ---
# This schema must match the output of your connector functions.
NORMALIZED_SCHEMA = {
    "message_id": None,
    "source_platform": None,
    "timestamp_utc": None,
    "text_content": None,
    "author_info": {},
    "original_url": None,
    "raw_metadata": {}
}

# --- Enriched Feedback Schema (Output after AI processing) ---
# This extends the normalized schema with AI-generated insights.
ENRICHED_SCHEMA = NORMALIZED_SCHEMA.copy()
ENRICHED_SCHEMA.update({
    "sentiment": None,               # e.g., "positive", "negative", "neutral"
    "category": None,                # e.g., "bug_report", "feature_request", "general_feedback", "negative_competitor"
    "detected_competitors": [],      # List of detected competitor names
    "auto_reply_text": None,         # Generated reply for positive feedback
    "processing_timestamp_utc": None # When AI processing occurred
})

# --- Dummy AI Logic & Competitor List ---
# In a real system, these would be sophisticated AI model calls.
# DUMMY_CATEGORIES = ["bug_report", "feature_request", "general_feedback"]
# DUMMY_SENTIMENTS = ["positive", "negative", "neutral"]
# DUMMY_COMPETITORS = ["Asana", "Monday.com", "ClickUp", "Trello"]

# --- Custom Categories for Natural Language AI (Conceptual) ---
# In a real setup, you would train a custom text classification model in Natural Language AI
# or Vertex AI AutoML with your own labels (e.g., 'bug_report', 'feature_request', 'general_feedback').
# For this example, we'll use a combination of pre-trained NLP sentiment and keyword matching for categories.

# --- Competitor List for Entity Detection (Conceptual) ---
# In a real setup, you'd manage this list (e.g., from a database or config)
# or potentially train a custom entity extraction model in Natural Language AI / Vertex AI.
COMPETITOR_KEYWORDS = ["asana", "monday.com", "clickup", "trello", "jira", "basecamp"] # Lowercase for matching

def analyze_text_with_nlp(text_content):
    """
    Uses Google Cloud Natural Language API for sentiment and entity analysis.
    Returns detected sentiment, entities, and attempts a basic category.
    """
    document = language_v1.Document(content=text_content, type_=language_v1.Document.Type.PLAIN_TEXT)

    # Sentiment Analysis
    sentiment_response = nlp_client.analyze_sentiment(document=document)
    sentiment_score = sentiment_response.document_sentiment.score # -1.0 to 1.0
    sentiment_magnitude = sentiment_response.document_sentiment.magnitude # 0.0 to +inf
    sentiment = "neutral"
    if sentiment_score >= 0.2:
        sentiment = "positive"
    elif sentiment_score <= -0.2:
        sentiment = "negative"

    # Entity Analysis (to help with competitor detection and other keywords)
    entity_response = nlp_client.analyze_entities(document=document, encoding_type=language_v1.EncodingType.UTF8)
    detected_competitors = []
    text_lower = text_content.lower()

    for comp_keyword in COMPETITOR_KEYWORDS:
        if comp_keyword in text_lower:
            detected_competitors.append(comp_keyword)

    # Simple keyword-based category assignment after NLP (can be replaced by custom NLP classification)
    category = "general_feedback"
    if "bug" in text_lower or "crash" in text_lower or "error" in text_lower or "laggy" in text_lower:
        category = "bug_report"
    elif "feature" in text_lower or "idea" in text_lower or "wish" in text_lower or "suggestion" in text_lower:
        category = "feature_request"

    if sentiment == "negative" and detected_competitors:
        category = "negative_competitor_review" # Prioritize this specific negative category

    return sentiment, category, detected_competitors

def generate_auto_reply_with_gemini(original_text, sentiment, category):
    """
    Uses Vertex AI (Gemini API) to generate an automated reply for positive feedback.
    """
    if sentiment == "positive" and category != "bug_report": # Don't auto-reply to positive bug reports (usually need human review)
        prompt_text = (
            f"You are a helpful and appreciative customer support bot for FlowHub. "
            f"A customer left the following positive feedback: '{original_text}'. "
            f"Write a short, friendly, and grateful thank you message. "
            f"Do not ask questions or offer further help unless specifically related to their positive comment. "
            f"Keep it concise, under 50 words."
        )
        try:
            # Generate content using Gemini
            # For demonstration, we'll use generate_content which is synchronous.
            # For production, consider async calls or batching if high volume.
            response = gemini_model.generate_content([Part.from_text(prompt_text)])
            return response.text.strip()
        except Exception as e:
            print(f"ERROR: Gemini API call failed: {e}")
            return "Thank you for your feedback!" # Fallback reply
    return None

def ai_processor_entrypoint(event, context):
    """
    Cloud Function entry point for the AI Processor.
    Triggered by new messages in the 'raw-feedback-toc' Pub/Sub topic.
    """
    print(f"AI Processor triggered. Project: {PROJECT_ID}, Raw Topic: {RAW_FEEDBACK_TOPIC_NAME}, Classified Topic: {CLASSIFIED_FEEDBACK_TOPIC_NAME}")

    if not event or not 'data' in event:
        print("No data in Pub/Sub message. Exiting.")
        return

    try:
        # Pub/Sub message data is Base64 encoded
        message_data_b64 = event['data']
        decoded_data_str = base64.b64decode(message_data_b64).decode('utf-8')
        normalized_feedback = json.loads(decoded_data_str)

        if not all(key in normalized_feedback for key in NORMALIZED_SCHEMA):
            print(f"ERROR: Received message does not conform to normalized schema: {normalized_feedback}")
            return

        print(f"Processing message ID: {normalized_feedback.get('message_id')} from {normalized_feedback.get('source_platform')}")

        # --- REAL AI Processing with Google Cloud NLP & Vertex AI Gemini ---
        text_content = normalized_feedback.get("text_content", "")

        # 1. Natural Language API for Sentiment, Category & Entity Detection
        sentiment, category, detected_competitors = analyze_text_with_nlp(text_content)

        # 2. Vertex AI Gemini for Auto-Reply Generation
        auto_reply_text = generate_auto_reply_with_gemini(text_content, sentiment, category)

        # --- Construct Enriched Feedback ---
        enriched_feedback = normalized_feedback.copy()
        enriched_feedback.update({
            "sentiment": sentiment,
            "category": category,
            "detected_competitors": detected_competitors,
            "auto_reply_text": auto_reply_text,
            "processing_timestamp_utc": datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        })

        # --- Publish to Classified Feedback Topic ---
        classified_data_bytes = json.dumps(enriched_feedback).encode('utf-8')
        future = publisher.publish(classified_feedback_topic_path, classified_data_bytes)
        classified_message_id = future.result()
        print(f"Published enriched message {classified_message_id} to classified-feedback-topics. Category: {category}, Sentiment: {sentiment}")

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from Pub/Sub message: {e}. Raw data: {message_data_b64}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during AI processing: {e}")
        # In a real system, you might want to log the full traceback for debugging

