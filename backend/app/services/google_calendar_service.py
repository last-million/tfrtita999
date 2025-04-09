import logging
import os
import json
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..config import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """
    Service to handle Google Calendar API integration.
    Allows creation, reading, and management of calendar events.
    """
    
    def __init__(self):
        self.is_configured = settings.google_calendar_enabled and settings.google_client_id and settings.google_client_secret
        self.credentials_file = settings.calendar_credentials_file
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.api_service_name = "calendar"
        self.api_version = "v3"
        
        # Scopes for Google Calendar API
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
        
        if not self.is_configured:
            logger.warning("Google Calendar is not configured. Calendar functionality will not work.")
    
    async def create_event(self, user_credentials: Dict, event_details: Dict) -> Dict[str, Any]:
        """
        Create a calendar event
        
        Args:
            user_credentials: OAuth credentials for the user
            event_details: Details for the event
                - summary: Event title
                - location: Event location (optional)
                - description: Event description (optional)
                - start_time: Start time (ISO format)
                - end_time: End time (ISO format)
                - attendees: List of email addresses (optional)
                - timezone: Timezone (default: UTC)
                
        Returns:
            Event details if successful, error information if not
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Google Calendar is not configured"
            }
            
        try:
            # Create calendar API client
            credentials = self._get_credentials(user_credentials)
            service = build(self.api_service_name, self.api_version, credentials=credentials)
            
            # Format event
            event = {
                'summary': event_details.get('summary', 'Meeting'),
                'location': event_details.get('location', ''),
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': event_details.get('start_time'),
                    'timeZone': event_details.get('timezone', 'UTC'),
                },
                'end': {
                    'dateTime': event_details.get('end_time'),
                    'timeZone': event_details.get('timezone', 'UTC'),
                },
            }
            
            # Add attendees if provided
            if event_details.get('attendees'):
                event['attendees'] = [{'email': email} for email in event_details['attendees']]
            
            # Add conferencing (Google Meet) if requested
            if event_details.get('add_conferencing', True):
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meeting-{datetime.now().timestamp()}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            
            # Create event
            event = service.events().insert(
                calendarId='primary', 
                body=event,
                conferenceDataVersion=1 if event_details.get('add_conferencing', True) else 0
            ).execute()
            
            return {
                "success": True,
                "event_id": event.get('id'),
                "summary": event.get('summary'),
                "start_time": event.get('start', {}).get('dateTime'),
                "end_time": event.get('end', {}).get('dateTime'),
                "hangout_link": event.get('hangoutLink'),
                "html_link": event.get('htmlLink')
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create calendar event: {str(e)}"
            }
    
    async def get_upcoming_events(self, user_credentials: Dict, max_results: int = 10) -> Dict[str, Any]:
        """
        Get upcoming events from the user's primary calendar
        
        Args:
            user_credentials: OAuth credentials for the user
            max_results: Maximum number of events to return
            
        Returns:
            List of upcoming events if successful, error information if not
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Google Calendar is not configured"
            }
            
        try:
            # Create calendar API client
            credentials = self._get_credentials(user_credentials)
            service = build(self.api_service_name, self.api_version, credentials=credentials)
            
            # Get current time in ISO format
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
            # Get events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    "id": event['id'],
                    "summary": event.get('summary', 'No title'),
                    "start": start,
                    "end": end,
                    "location": event.get('location', ''),
                    "description": event.get('description', ''),
                    "hangout_link": event.get('hangoutLink'),
                    "html_link": event.get('htmlLink')
                })
            
            return {
                "success": True,
                "events": formatted_events
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar events: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get calendar events: {str(e)}"
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
    
    def extract_event_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract event details from natural language text
        Uses a simple rule-based approach for demonstration
        
        Args:
            text: Natural language text describing an event
            
        Returns:
            Event details if successful, empty dict if not
        """
        # This is a very simple implementation and would be more sophisticated in production
        event = {
            'summary': 'Meeting',
            'description': text,
            'location': '',
            'timezone': 'UTC',
            'attendees': []
        }
        
        # Set default time to tomorrow at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        event['start_time'] = tomorrow.isoformat()
        event['end_time'] = (tomorrow + timedelta(hours=1)).isoformat()
        
        # Look for potential meeting info in text
        lines = text.lower().split('\n')
        for line in lines:
            if 'meeting with' in line or 'meet with' in line:
                words = line.split()
                for i, word in enumerate(words):
                    if word in ['with', 'and'] and i+1 < len(words):
                        event['summary'] = f"Meeting with {words[i+1].title()}"
                        break
            
            # Very basic email extraction (would use regex in production)
            if '@' in line and '.' in line:
                for word in line.split():
                    if '@' in word and '.' in word:
                        event['attendees'].append(word.strip(',.;:'))
        
        return event

# Create singleton instance
google_calendar_service = GoogleCalendarService()
