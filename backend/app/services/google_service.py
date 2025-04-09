import logging
import os
import json
from typing import Dict, List, Any, Optional, Union
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleService:
    """
    Service for interacting with Google APIs, particularly Google Sheets
    """
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
    async def list_sheets(self, credentials_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        List all Google Sheets accessible to the user
        """
        try:
            # Create credentials from dictionary
            credentials = self._create_credentials(credentials_dict)
            
            # Build the Drive API client to find sheets
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Query for sheets files only
            query = "mimeType='application/vnd.google-apps.spreadsheet'"
            fields = "files(id, name, createdTime, modifiedTime)"
            
            response = drive_service.files().list(
                q=query,
                spaces='drive',
                fields=fields,
                pageSize=100
            ).execute()
            
            sheets = []
            for file in response.get('files', []):
                sheets.append({
                    "id": file.get("id"),
                    "name": file.get("name"),
                    "created_at": file.get("createdTime"),
                    "modified_at": file.get("modifiedTime")
                })
                
            return sheets
        except Exception as e:
            logger.error(f"Error listing Google Sheets: {str(e)}")
            raise Exception(f"Google Sheets API error: {str(e)}")
    
    async def create_sheet(self, credentials_dict: Dict[str, Any], sheet_name: str) -> str:
        """
        Create a new Google Sheet with the given name
        Returns the ID of the new sheet
        """
        try:
            # Create credentials from dictionary
            credentials = self._create_credentials(credentials_dict)
            
            # Build the Sheets API client
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            # Create a new spreadsheet
            spreadsheet = {
                'properties': {
                    'title': sheet_name
                }
            }
            
            request = sheets_service.spreadsheets().create(body=spreadsheet)
            response = request.execute()
            
            return response['spreadsheetId']
        except Exception as e:
            logger.error(f"Error creating Google Sheet: {str(e)}")
            raise Exception(f"Google Sheets API error: {str(e)}")
    
    async def get_sheet_columns(self, credentials_dict: Dict[str, Any], sheet_id: str) -> List[str]:
        """
        Get the column headers from the first row of a Google Sheet
        """
        try:
            # Create credentials from dictionary
            credentials = self._create_credentials(credentials_dict)
            
            # Build the Sheets API client
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            # Get the first row of the first sheet
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range="A1:Z1"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
                
            return values[0]
        except Exception as e:
            logger.error(f"Error getting Google Sheet columns: {str(e)}")
            raise Exception(f"Google Sheets API error: {str(e)}")
    
    async def update_sheet_values(
        self, 
        credentials_dict: Dict[str, Any], 
        sheet_id: str, 
        range_name: str, 
        values: List[List[Any]]
    ) -> int:
        """
        Update a range of cells in a Google Sheet
        """
        try:
            # Create credentials from dictionary
            credentials = self._create_credentials(credentials_dict)
            
            # Build the Sheets API client
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            body = {
                'values': values
            }
            
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return result.get('updatedCells')
        except Exception as e:
            logger.error(f"Error updating Google Sheet values: {str(e)}")
            raise Exception(f"Google Sheets API error: {str(e)}")
    
    async def append_sheet_values(
        self, 
        credentials_dict: Dict[str, Any], 
        sheet_id: str, 
        values: List[List[Any]]
    ) -> int:
        """
        Append rows to a Google Sheet
        """
        try:
            # Create credentials from dictionary
            credentials = self._create_credentials(credentials_dict)
            
            # Build the Sheets API client
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            body = {
                'values': values
            }
            
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range="A1",  # This range is just the starting point
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return result.get('updates', {}).get('updatedRows', 0)
        except Exception as e:
            logger.error(f"Error appending Google Sheet values: {str(e)}")
            raise Exception(f"Google Sheets API error: {str(e)}")
    
    def _create_credentials(self, credentials_dict: Dict[str, Any]) -> Credentials:
        """
        Create Google OAuth2 credentials from a dictionary
        """
        # Convert the credentials dictionary back to a Google OAuth2 credentials object
        return Credentials(
            token=credentials_dict.get('token'),
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=credentials_dict.get('client_id'),
            client_secret=credentials_dict.get('client_secret'),
            scopes=self.scopes
        )
