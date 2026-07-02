#!/usr/bin/env python3
import base64
import pickle
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("⚠️ Install: pip install google-auth google-auth-oauthlib google-api-python-client")
    raise

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    token_path = Path.home() / '.gmail_token.pickle'
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def send_email_with_resume(to, subject, body, resume_path):
    try:
        service = get_gmail_service()
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        if resume_path.exists():
            with open(resume_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='pdf')
                attachment.add_header('Content-Disposition', 'attachment', filename=resume_path.name)
                message.attach(attachment)
                print(f"📎 Attached: {resume_path.name}")
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"✅ Email sent to {to} (ID: {sent['id']})")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
