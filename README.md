InsightStream AI: Automated Customer Feedback Intelligence
Overview
InsightStream AI is a powerful, automated system designed to revolutionize how public-facing companies manage and act upon their customer feedback. Built on Google Cloud Platform, it transforms raw, unstructured feedback from various channels into actionable, categorized insights, driving efficiency and improving customer satisfaction.

The Problem
Companies today are overwhelmed by the sheer volume of customer feedback across social media, websites, email, and app stores. Manually sifting through this data for bug reports, feature requests, sentiment, and competitor mentions is a time-consuming, error-prone, and inefficient process, often leading to delayed responses and missed opportunities.

Our Solution: InsightStream AI
InsightStream AI provides an intelligent, automated pipeline that addresses these challenges head-on:

Automated Ingestion: Continuously collects feedback from diverse sources.

Intelligent AI Processing: Leverages cutting-edge AI to understand, categorize, and enrich every piece of feedback.

Actionable Integrations: Automatically routes categorized feedback to the right teams and responds to customers in real-time.

Persistent Insights: Stores all data in a structured database for deep analysis and reporting.

Key Features (Current MVP)
Multi-Channel Feedback Ingestion:

Automated collection of dummy data from Twitter (X).

Designed for easy expansion to TikTok, Website Forms, Email Inboxes, and App Store Reviews.

Advanced AI Processing:

Sentiment Analysis: Automatically determines if feedback is positive, negative, or neutral using Google Cloud Natural Language AI.

Category Classification: Intelligently tags feedback as bug_report, feature_request, general_feedback, or negative_competitor_review using Google Cloud Natural Language AI (with keyword enhancements).

Competitor Detection: Identifies mentions of competitor names within negative feedback.

Automated Reply Generation: Crafts personalized, human-like thank-you messages for positive feedback using Google Vertex AI (Gemini).

Robust & Scalable Cloud Architecture:

Built on a serverless, event-driven pipeline using Google Cloud Functions and Cloud Pub/Sub for reliability, decoupling, and automatic scaling.

Automated Integrations (Simulated):

Jira Integration: Automatically triggers the simulation of creating bug tickets for bug_report feedback.

Basecamp Integration: Automatically triggers the simulation of creating to-do items for feature_request feedback.

Email Reply Integration: Automatically triggers the simulation of sending personalized email replies for positive feedback.

Persistent Data Storage:

Stores all raw, normalized, and AI-enriched feedback in a cost-optimized Google Cloud SQL (PostgreSQL) database for comprehensive historical data and future analytics.

Automated Workflow:

Google Cloud Scheduler triggers the ingestion functions, ensuring a continuous, hands-off flow of feedback through the system.

Conceptual Architecture
InsightStream AI operates as a continuous data pipeline with distinct, interconnected zones:

The "Listening Post" (Data Ingestion): Collects raw feedback from external sources and queues it reliably via Pub/Sub.

The "Brain Trust" (Intelligent Processing): Consumes raw feedback, applies AI models (Google Cloud NLP, Vertex AI Gemini) for categorization, sentiment, entity detection, and reply generation, then re-queues the enriched data.

The "Action Squad" (Action & Integration): Listens for classified feedback and triggers automated actions in external systems like Jira, Basecamp, or email senders.

The "Memory & Insights Vault" (Data Storage & Analytics): Persistently stores all data in Cloud SQL, making it ready for querying, reporting, and dashboarding.

Technology Stack
Cloud Platform: Google Cloud Platform (GCP)

Serverless Compute: Google Cloud Functions (Python 3.11)

Messaging: Google Cloud Pub/Sub

Database: Google Cloud SQL (PostgreSQL)

AI/ML Services: Google Cloud Natural Language API, Google Vertex AI (Gemini Pro)

Orchestration: Google Cloud Scheduler

Programming Language: Python

Setup & Deployment (High-Level Steps)
This project is built around a fictitious SaaS company, ZenithFlow Solutions, and their product, FlowHub, with dummy data simulating real-world customer feedback.

Google Cloud Project Setup: Create a new GCP project (zenithflow-feedback-automation), enable billing, and enable necessary APIs (Pub/Sub, Cloud Functions, Cloud Build, Cloud Scheduler, Cloud Natural Language API, Vertex AI API).

Pub/Sub Topic Creation: Create two Pub/Sub topics: raw-feedback-toc (for raw normalized feedback) and classified-feedback-topics (for AI-enriched feedback).

Cloud SQL Setup: Create a cost-optimized Google Cloud SQL (PostgreSQL) instance (insightstream-db-public-dev) with Public IP enabled and your local development machine's IP whitelisted for secure access. Create a feedback_db database and feedback_user within this instance, and create the enriched_feedback table.

Cloud Function Deployment:

twitter_connector: Deployed as a Cloud Function (HTTP triggered by Cloud Scheduler) to generate and normalize dummy Twitter data, publishing to raw-feedback-toc.

ai_processor: Deployed as a Cloud Function (Pub/Sub triggered by raw-feedback-toc) to perform AI analysis and publish to classified-feedback-topics. Memory allocated to 512MB, and necessary IAM roles (Cloud AI Platform User, Vertex AI User, Service Usage Consumer) granted to its service account.

jira_integration: Deployed as a Cloud Function (Pub/Sub triggered by classified-feedback-topics) to simulate Jira issue creation for bug reports, with Pub/Sub Subscriber IAM role.

email_reply_integration: Deployed as a Cloud Function (Pub/Sub triggered by classified-feedback-topics) to simulate sending email replies for positive feedback, with Pub/Sub Subscriber IAM role.

basecamp_integration: Deployed as a Cloud Function (Pub/Sub triggered by classified-feedback-topics) to simulate creating Basecamp to-dos for feature requests, with Pub/Sub Subscriber IAM role.

Local Data Listener: A local Python script (local_db_writer.py) running on your machine subscribes to classified-feedback-topics and writes the enriched data into the Cloud SQL database. This avoids VPC Connector costs for development.

Automated Trigger: A Google Cloud Scheduler job is configured to trigger the twitter_connector Cloud Function on a set frequency (e.g., every 5 minutes), automating the entire pipeline.

Future Vision: Towards an Agentic AI SaaS App
This project serves as a robust foundation. The next exciting phase is to transform InsightStream AI into a full-fledged SaaS application that leverages Agentic AI. This will involve:

Building a user-friendly web interface for customers to onboard, configure integrations, and view advanced analytics.

Developing AI agents that can perform more complex tasks like identifying emerging trends, suggesting proactive customer outreach, optimizing workflows, or even engaging in multi-turn conversations.

Implementing a robust user authentication and authorization system.

Exploring advanced data visualization and reporting.

Getting Started (Local Development)
Clone this repository.

Set up a Python virtual environment: python -m venv venv && source venv/bin/activate

Install local dependencies: pip install -r requirements.txt (from root for local_db_writer.py).

Follow the detailed deployment steps above (or in specific function directories) to deploy Cloud Functions to your GCP project.

Ensure gcloud auth application-default login is run locally for your local_db_writer.py to authenticate with Google Cloud.

Run python local_db_writer.py to start local listening and database writing.

Contact
For questions or further collaboration, please contact [Your Name/Email/GitHu