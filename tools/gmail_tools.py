import os
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config.settings import settings
from langchain_community.tools import  Tool

logger = logging.getLogger(__name__)

SCOPES = [settings.SCOPES]
GMAIL_TOKEN_PATH = settings.GMAIL_TOKEN_PATH
GMAIL_CREDENTIALS_PATH = settings.GMAIL_CREDENTIALS_PATH

def get_gmail_service():
    try:
        creds = None

        if os.path.exists(GMAIL_TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading authorized user file from {GMAIL_TOKEN_PATH}: {e}. Re-authenticating...")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}. Removing token file and re-authenticating.")
                    if os.path.exists(GMAIL_TOKEN_PATH):
                        try:
                            os.remove(GMAIL_TOKEN_PATH)
                        except Exception:
                            pass
                    creds = None

            if not creds:
                if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Google OAuth client secrets file '{GMAIL_CREDENTIALS_PATH}' is missing. "
                        "Please place your credentials.json file in the root directory to initiate OAuth authentication."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            os.makedirs(os.path.dirname(GMAIL_TOKEN_PATH), exist_ok=True)
            with open(GMAIL_TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        return f"error in calling gmail: {e}"


def fetch_recent_emails(max_results=10, label="INBOX", q=None):
    try:
        service = get_gmail_service()
        if isinstance(service, str):
            # If error string is returned from get_gmail_service
            raise Exception(service)

        label_ids = [label] if label else None
        results = service.users().messages().list(
            userId="me", maxResults=max_results, labelIds=label_ids, q=q
        ).execute()
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            msg_detail = service.users().messages().get(userId="me", id=msg["id"]).execute()

            headers = msg_detail["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "(unknown sender)")
            date = next((h["value"] for h in headers if h["name"] == "Date"), "(unknown date)")

            # Extract body if possible, default to snippet
            body = msg_detail.get("snippet", "")
            emails.append({
                "id": msg["id"],
                "subject": subject,
                "sender": sender,
                "date": date,
                "snippet": msg_detail.get("snippet", ""),
                "body": body
            })

        return emails
    except Exception as e:
        return f"error in retrieving email from gmail : {e}"


def fetch_single_email(msg_id):
    try:
        service = get_gmail_service()
        if isinstance(service, str):
            raise Exception(service)

        msg_detail = service.users().messages().get(userId="me", id=msg_id).execute()
        headers = msg_detail["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(unknown sender)")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "(unknown date)")

        body = msg_detail.get("snippet", "")
        # Attempt to extract full body
        payload = msg_detail.get("payload", {})
        parts = payload.get("parts", [])
        body_data = ""
        if not parts:
            body_data = payload.get("body", {}).get("data", "")
        else:
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    body_data = part.get("body", {}).get("data", "")
                    break
            if not body_data:
                body_data = parts[0].get("body", {}).get("data", "")

        if body_data:
            import base64
            try:
                body = base64.urlsafe_b64decode(body_data).decode("utf-8")
            except Exception:
                pass

        return {
            "id": msg_id,
            "subject": subject,
            "sender": sender,
            "date": date,
            "snippet": msg_detail.get("snippet", ""),
            "body": body
        }
    except Exception as e:
        return f"error: {e}"
#
# gmail_tool = Tool(
#     func= fetch_recent_emails,
#     name= "gmail_tool",
#     description=  "use it when user ask summary of his gmail or anything related to gmail"
# )