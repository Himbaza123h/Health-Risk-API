
import logging
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from . import GoogleSheetsClient, RiskCalculator
from .. import models

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.sheets_client = GoogleSheetsClient()
        self.risk_calculator = RiskCalculator()

    async def sync_data(self, last_sync: Optional[datetime] = None) -> Dict:
        """
        Synchronize data from Google Sheets to local database
        Returns summary of sync operation
        """
        try:
            # Get new entries from Google Sheets
            new_entries = self.sheets_client.get_new_entries(last_sync)
            
            if not new_entries:
                return {"status": "success", "message": "No new entries found", "processed": 0}

            processed = 0
            errors = []

            # Process each entry
            for entry in new_entries:
                try:
                    # Calculate risk scores
                    insurance_risk = self.risk_calculator.calculate_insurance_risk(entry)
                    diabetes_risk = self.risk_calculator.calculate_diabetes_risk(entry)

                    # Prepare user data model
                    user_data = models.UserData(
                        **entry,
                        insurance_risk_score=insurance_risk,
                        diabetes_risk_score=diabetes_risk
                    )

                    # Add to database
                    self.db.add(user_data)
                    self.db.commit()
                    
                    # Log risk assessment
                    risk_log = models.RiskAssessmentLog(
                        user_id=user_data.id,
                        assessment_type='both',
                        insurance_risk_score=insurance_risk,
                        diabetes_risk_score=diabetes_risk,
                        factors=entry
                    )
                    self.db.add(risk_log)
                    self.db.commit()

                    processed += 1

                except Exception as e:
                    error_msg = f"Error processing entry: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    self.db.rollback()

            return {
                "status": "success",
                "message": f"Processed {processed} entries",
                "processed": processed,
                "errors": errors if errors else None
            }

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "processed": 0
            }