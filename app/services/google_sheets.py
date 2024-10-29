from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class GoogleSheetsClient:
    def __init__(self):
        self.creds = None
        self.SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
        self.USER_DATA_RANGE = os.getenv('USER_DATA_SHEET_RANGE', 'user_data!A2:Z')
        self.HEALTH_ACTIVITIES_RANGE = os.getenv('HEALTH_ACTIVITIES_SHEET_RANGE', 'health_activities!A2:Z')
        self.RISK_ASSESSMENT_LOGS_RANGE = os.getenv('RISK_ASSESSMENT_LOGS_SHEET_RANGE', 'risk_assessment_logs!A2:Z')

    def authenticate(self):
        """Handles Google Sheets OAuth authentication."""
        # Your existing authentication code here

    def get_entries(self, sheet_type: str, last_timestamp: datetime = None) -> List[Dict[Any, Any]]:
        """
        Retrieves entries from the specified Google Sheets sheet.
        Args:
            sheet_type (str): The type of sheet ('user_data', 'health_activities', 'risk_assessment_logs').
            last_timestamp (datetime): Filter entries after this timestamp.
        Returns:
            List[Dict]: List of formatted user data dictionaries.
        """
        try:
            self.authenticate()
            service = build('sheets', 'v4', credentials=self.creds)

            # Determine the range based on the sheet type
            if sheet_type == 'user_data':
                range_name = self.USER_DATA_RANGE
            elif sheet_type == 'health_activities':
                range_name = self.HEALTH_ACTIVITIES_RANGE
            elif sheet_type == 'risk_assessment_logs':
                range_name = self.RISK_ASSESSMENT_LOGS_RANGE
            else:
                logger.error('Invalid sheet type provided.')
                return []

            # Fetch data from the specified sheet
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()

            values = result.get('values', [])
            if not values:
                logger.info(f'No data found in {sheet_type} sheet.')
                return []

            # Process the data based on the sheet type
            # Here you will need to adapt your DataFrame processing code as needed

            logger.info(f'Successfully retrieved {len(values) - 1} entries from {sheet_type}.')
            return values[1:]  # Return the data excluding the header row

        except Exception as e:
            logger.error(f'Error retrieving data from {sheet_type} sheet: {str(e)}')
            raise
