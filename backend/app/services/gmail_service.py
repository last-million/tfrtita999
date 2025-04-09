import logging
import os
import json
import base64
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)

class GmailService:
    """
    Service to handle Gmail API integration.
    Allows sending emails and accessing email data.
    """
    
    def __init__(self):
        self.is_configured = settings.gmail_enabled and settings.google_client_id and settings.google_client_secret
        self.credentials_file = settings.gmail_credentials_file
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.api_service_name = "gmail"
        self.api_version = "v1"
        
        # Scopes for Gmail API
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly"
        ]
        
        if not self.is_configured:
            logger.warning("Gmail API is not configured. Email functionality will not work.")
    
    async def send_email(self, user_credentials: Dict, email_details: Dict) -> Dict[str, Any]:
        """
        Send an email using Gmail API
        
        Args:
            user_credentials: OAuth credentials for the user
            email_details: Details for the email
                - to: Recipient email address or list of addresses
                - subject: Email subject
                - body: Email body
                - body_type: 'plain' or 'html'
                - cc: CC recipients (optional)
                - bcc: BCC recipients (optional)
                
        Returns:
            Email details if successful, error information if not
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Gmail API is not configured"
            }
            
        try:
            # Create Gmail API client
            credentials = self._get_credentials(user_credentials)
            service = build(self.api_service_name, self.api_version, credentials=credentials)
            
            # Create email message
            message = self._create_message(
                to=email_details.get('to', []),
                subject=email_details.get('subject', ''),
                body=email_details.get('body', ''),
                body_type=email_details.get('body_type', 'plain'),
                cc=email_details.get('cc', []),
                bcc=email_details.get('bcc', [])
            )
            
            # Send email
            sent_message = service.users().messages().send(
                userId="me",
                body=message
            ).execute()
            
            return {
                "success": True,
                "email_id": sent_message.get('id'),
                "thread_id": sent_message.get('threadId'),
                "to": email_details.get('to'),
                "subject": email_details.get('subject')
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }
    
    async def get_recent_emails(self, user_credentials: Dict, max_results: int = 10) -> Dict[str, Any]:
        """
        Get recent emails from the user's inbox
        
        Args:
            user_credentials: OAuth credentials for the user
            max_results: Maximum number of emails to return
            
        Returns:
            List of recent emails if successful, error information if not
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Gmail API is not configured"
            }
            
        try:
            # Create Gmail API client
            credentials = self._get_credentials(user_credentials)
            service = build(self.api_service_name, self.api_version, credentials=credentials)
            
            # Get emails
            results = service.users().messages().list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Format emails
            formatted_emails = []
            for message in messages:
                # Get full message
                msg = service.users().messages().get(
                    userId="me",
                    id=message['id']
                ).execute()
                
                # Extract headers
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
                from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
                
                # Add to formatted emails
                formatted_emails.append({
                    "id": msg['id'],
                    "thread_id": msg['threadId'],
                    "subject": subject,
                    "from": from_email,
                    "date": date,
                    "snippet": msg.get('snippet', '')
                })
            
            return {
                "success": True,
                "emails": formatted_emails
            }
            
        except Exception as e:
            logger.error(f"Error getting emails: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get emails: {str(e)}"
            }
    
    def _get_credentials(self, user_credentials: Dict) -> Credentials:
        """
        Get Google API credentials from user-provided credentials
        
        Args:
            user_credentials: User credentials from database
            
        Returns:
            Google API credentials
        """
        creds_data = user_credentials.get('token_data', {})
        
        # Create credentials object
        credentials = Credentials(
            token=creds_data.get('access_token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )
        
        # Refresh if expired
        if credentials.expired:
            credentials.refresh(Request())
        
        return credentials
    
    def _create_message(self, to, subject, body, body_type='plain', cc=None, bcc=None):
        """
        Create a Gmail API message
        
        Args:
            to: Recipient(s)
            subject: Email subject
            body: Email body
            body_type: 'plain' or 'html'
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            
        Returns:
            Gmail API message object
        """
        # Create message container
        message = MIMEMultipart()
        message['to'] = self._format_recipients(to)
        message['subject'] = subject
        
        # Add CC and BCC if provided
        if cc:
            message['cc'] = self._format_recipients(cc)
        if bcc:
            message['bcc'] = self._format_recipients(bcc)
        
        # Attach body
        if body_type.lower() == 'html':
            message.attach(MIMEText(body, 'html'))
        else:
            message.attach(MIMEText(body, 'plain'))
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        return {'raw': raw_message}
    
    def _format_recipients(self, recipients):
        """
        Format recipients for email headers
        
        Args:
            recipients: Single email address or list of addresses
            
        Returns:
            Comma-separated string of email addresses
        """
        if isinstance(recipients, list):
            return ', '.join(recipients)
        return recipients
    
    def get_auth_url(self) -> str:
        """
        Get Google OAuth authorization URL
        
        Returns:
            Authorization URL
        """
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [f"https://{settings.server_domain}/api/auth/google/callback"],
                }
            },
            scopes=self.scopes
        )
        
        # Set redirect URI
        flow.redirect_uri = f"https://{settings.server_domain}/api/auth/google/callback"
        
        # Generate URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return auth_url
    
    def extract_email_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract email details from natural language text
        Uses a simple rule-based approach for demonstration
        
        Args:
            text: Natural language text describing an email
            
        Returns:
            Email details if successful, empty dict if not
        """
        # This is a very simple implementation and would be more sophisticated in production
        email = {
            'subject': 'Email from Call',
            'body': text,
            'body_type': 'plain',
            'to': [],
            'cc': [],
            'bcc': []
        }
        
        # Look for potential email info in text
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            
            # Check for subject
            if line_lower.startswith('subject:') or 'subject is' in line_lower or 'subject:' in line_lower:
                parts = line.split(':', 1) if ':' in line else line.split('is', 1)
                if len(parts) > 1:
                    email['subject'] = parts[1].strip()
            
            # Check for recipients
            if '@' in line and '.' in line:
                if 'to:' in line_lower or 'send to' in line_lower or 'email to' in line_lower:
                    for word in line.split():
                        if '@' in word and '.' in word:
                            email['to'].append(word.strip(',.;:'))
                elif 'cc:' in line_lower:
                    for word in line.split():
                        if '@' in word and '.' in word:
                            email['cc'].append(word.strip(',.;:'))
                elif 'bcc:' in line_lower:
                    for word in line.split():
                        if '@' in word and '.' in word:
                            email['bcc'].append(word.strip(',.;:'))
                elif not email['to']:  # Default case, if no specific recipient type mentioned
                    for word in line.split():
                        if '@' in word and '.' in word:
                            email['to'].append(word.strip(',.;:'))
        
        # If no recipients found, return empty dict
        if not email['to']:
            return {}
            
        return email

# Create singleton instance
gmail_service = GmailService()
