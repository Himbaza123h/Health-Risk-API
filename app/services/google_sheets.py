from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import pickle
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self.SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
        if not self.SPREADSHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID environment variable not set")
            
        self.RANGES = {
            'user_data': os.getenv('USER_DATA_SHEET_RANGE', 'user_data!A2:Z'),
            'health_activities': os.getenv('HEALTH_ACTIVITIES_SHEET_RANGE', 'health_activities!A2:Z'),
            'risk_assessment_logs': os.getenv('RISK_ASSESSMENT_LOGS_SHEET_RANGE', 'risk_assessment_logs!A2:Z')
        }
        
        # Ensure config directory exists
        self.config_dir = Path('config')
        self.config_dir.mkdir(exist_ok=True)
        
        self.credentials_path = self.config_dir / 'credentials.json'
        self.token_path = self.config_dir / 'token.pickle'

    def authenticate(self) -> bool:
        """
        Handles Google Sheets authentication
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"credentials.json not found in {self.credentials_path}. "
                            "Please download OAuth 2.0 credentials from Google Cloud Console"
                        )
                    
                    logger.info("Initiating OAuth2 authentication flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for future use
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('sheets', 'v4', credentials=self.creds)
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def update_sheets(self, data: Dict[str, List[List[str]]]) -> Dict[str, Any]:
        """
        Updates multiple sheets with their respective data
        
        Args:
            data (Dict[str, List[List[str]]]): Dictionary with sheet names as keys and data as values
        
        Returns:
            Dict[str, Any]: Status of updates for each sheet
        """
        results = {}
        
        if not self.authenticate():
            raise Exception("Failed to authenticate with Google Sheets")

        try:
            for sheet_name, values in data.items():
                if not values:
                    logger.warning(f"No data provided for sheet: {sheet_name}")
                    results[sheet_name] = {"status": "skipped", "reason": "no data"}
                    continue

                range_name = self.RANGES.get(sheet_name)
                if not range_name:
                    logger.warning(f"No range defined for sheet: {sheet_name}")
                    results[sheet_name] = {"status": "skipped", "reason": "no range defined"}
                    continue

                try:
                    # Clear existing data
                    clear_request = {
                        'ranges': [range_name]
                    }
                    self.service.spreadsheets().values().batchClear(
                        spreadsheetId=self.SPREADSHEET_ID,
                        body=clear_request
                    ).execute()

                    # Update with new data
                    body = {
                        'values': values
                    }
                    update_result = self.service.spreadsheets().values().update(
                        spreadsheetId=self.SPREADSHEET_ID,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()

                    results[sheet_name] = {
                        "status": "success",
                        "rows_updated": len(values),
                        "cells_updated": update_result.get('updatedCells', 0)
                    }
                    logger.info(f"Successfully updated {sheet_name} with {len(values)} rows")

                except HttpError as e:
                    error_message = e.error_details[0]['message'] if e.error_details else str(e)
                    results[sheet_name] = {
                        "status": "error",
                        "error": error_message
                    }
                    logger.error(f"Error updating {sheet_name}: {error_message}")

            return results

        except Exception as e:
            logger.error(f"Error in update_sheets: {str(e)}")
            raise


    def test_connection(self) -> Dict[str, Any]:
        """
        Tests the connection to Google Sheets and verifies access to the spreadsheet
        
        Returns:
            Dict[str, Any]: Connection test results
        """
        try:
            if not self.authenticate():
                return {
                    "status": "error",
                    "message": "Authentication failed"
                }

            # Try to get spreadsheet metadata
            result = self.service.spreadsheets().get(
                spreadsheetId=self.SPREADSHEET_ID
            ).execute()

            return {
                "status": "success",
                "spreadsheet_title": result.get('properties', {}).get('title', ''),
                "sheets": [sheet['properties']['title'] for sheet in result.get('sheets', [])]
            }

        except HttpError as e:
            error_message = e.error_details[0]['message'] if e.error_details else str(e)
            return {
                "status": "error",
                "message": f"Google Sheets API error: {error_message}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
        


    def get_sheet_data(self, sheet_type: str) -> List[Dict]:
        """
        Retrieves data from Google Sheets
        
        Args:
            sheet_type (str): Type of sheet to read from
            
        Returns:
            List[Dict]: List of entries from the sheet
        """
        if not self.authenticate():
            raise Exception("Failed to authenticate with Google Sheets")

        try:
            logger.info(f"Fetching data for sheet type: {sheet_type}")
            
            range_name = self.RANGES.get(sheet_type)
            if not range_name:
                raise ValueError(f"No range defined for sheet type: {sheet_type}")

            logger.info(f"Using range: {range_name}")
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()

            values = result.get('values', [])
            logger.info(f"Retrieved {len(values)} rows from sheet")
            
            if not values:
                logger.warning("No data found in sheet")
                return []

            # First row contains headers
            headers = [h.lower().strip() for h in values[0]]
            entries = []

            # Process each row after headers
            for row in values[1:]:
                # Pad row with empty strings if it's shorter than headers
                row_data = row + [''] * (len(headers) - len(row))
                entry = dict(zip(headers, row_data))
                entries.append(entry)

            logger.info(f"Processed {len(entries)} entries from sheet")
            return entries

        except Exception as e:
            logger.error(f"Error getting sheet data: {str(e)}")
            raise