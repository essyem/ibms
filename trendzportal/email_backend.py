# trendzportal/email_backend.py
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import requests
from requests_oauthlib import OAuth2Session
import logging

logger = logging.getLogger(__name__)


class Office365EmailBackend(BaseEmailBackend):
    """
    Office 365 OAuth2 Email Backend for Django
    Uses Microsoft Graph API to send emails via Office 365
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.client_id = getattr(settings, 'OAUTH2_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'OAUTH2_CLIENT_SECRET', None)
        self.tenant_id = getattr(settings, 'OAUTH2_TENANT_ID', None)
        self.sender_email = getattr(settings, 'OAUTH2_SENDER_EMAIL', None)
        
        if not all([self.client_id, self.client_secret, self.tenant_id, self.sender_email]):
            logger.error("Missing Office 365 OAuth2 configuration")
            if not self.fail_silently:
                raise ValueError("Office 365 OAuth2 configuration is incomplete")
    
    def get_access_token(self):
        """Get access token using client credentials flow"""
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            logger.error(f"Failed to get Office 365 access token: {e}")
            if not self.fail_silently:
                raise
            return None
    
    def send_messages(self, email_messages):
        """Send email messages via Microsoft Graph API"""
        if not email_messages:
            return 0
        
        access_token = self.get_access_token()
        if not access_token:
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            try:
                if self._send_message(message, access_token):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                if not self.fail_silently:
                    raise
        
        return sent_count
    
    def _send_message(self, message, access_token):
        """Send a single email message"""
        try:
            # Prepare the email data for Microsoft Graph API
            email_data = {
                "message": {
                    "subject": message.subject,
                    "body": {
                        "contentType": "HTML" if message.content_subtype == 'html' else "Text",
                        "content": message.body
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": recipient}} 
                        for recipient in message.to
                    ],
                    "from": {
                        "emailAddress": {
                            "address": self.sender_email
                        }
                    }
                },
                "saveToSentItems": "true"
            }
            
            # Add CC recipients if any
            if message.cc:
                email_data["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": recipient}} 
                    for recipient in message.cc
                ]
            
            # Add BCC recipients if any
            if message.bcc:
                email_data["message"]["bccRecipients"] = [
                    {"emailAddress": {"address": recipient}} 
                    for recipient in message.bcc
                ]
            
            # Send via Microsoft Graph API
            graph_url = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                graph_url, 
                headers=headers, 
                json=email_data,
                timeout=getattr(settings, 'EMAIL_TIMEOUT', 30)
            )
            
            response.raise_for_status()
            
            logger.info(f"Email sent successfully to {', '.join(message.to)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via Graph API: {e}")
            if not self.fail_silently:
                raise
            return False


class ConsoleEmailBackend(BaseEmailBackend):
    """
    Fallback email backend that prints emails to console
    Used for development when Office 365 is not available
    """
    
    def send_messages(self, email_messages):
        """Print email messages to console"""
        if not email_messages:
            return 0
        
        for message in email_messages:
            print("\n" + "="*80)
            print("📧 EMAIL MESSAGE")
            print("="*80)
            print(f"From: {message.from_email}")
            print(f"To: {', '.join(message.to)}")
            if message.cc:
                print(f"CC: {', '.join(message.cc)}")
            if message.bcc:
                print(f"BCC: {', '.join(message.bcc)}")
            print(f"Subject: {message.subject}")
            print("-"*80)
            print("Body:")
            print(message.body)
            print("="*80)
        
        return len(email_messages)


class SmartEmailBackend(BaseEmailBackend):
    """
    Smart email backend that tries Office 365 first, falls back to console
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.office365_backend = Office365EmailBackend(fail_silently=True, **kwargs)
        self.console_backend = ConsoleEmailBackend(fail_silently=fail_silently, **kwargs)
    
    def send_messages(self, email_messages):
        """Try Office 365 first, fallback to console"""
        try:
            # Try Office 365 backend
            sent_count = self.office365_backend.send_messages(email_messages)
            if sent_count > 0:
                logger.info(f"Sent {sent_count} emails via Office 365")
                return sent_count
        except Exception as e:
            logger.warning(f"Office 365 backend failed, falling back to console: {e}")
        
        # Fallback to console backend
        logger.info("Using console backend for email")
        return self.console_backend.send_messages(email_messages)