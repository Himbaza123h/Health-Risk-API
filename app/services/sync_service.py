import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from .google_sheets import GoogleSheetsClient
from .risk_calculator import RiskCalculator
from .. import models

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.sheets_client = GoogleSheetsClient()
        self.risk_calculator = RiskCalculator()

        
    async def sync_from_sheets(self, last_sync: Optional[datetime] = None) -> Dict:
        """Sync data from Google Sheets to database"""
        sync_log = None
        try:
            # Create sync log
            sync_log = models.RiskAssessmentLog(
                assessment_type="sheets_to_db_sync",
                sync_start_time=datetime.utcnow(),
                sync_status="in_progress"
            )
            self.db.add(sync_log)
            self.db.commit()
            
            logger.info(f"Attempting to fetch sheet data. Last sync: {last_sync}")
            
            # Get sheet data
            sheet_data = self.sheets_client.get_sheet_data('user_data')
            
            # Log the retrieved data
            logger.info(f"Retrieved {len(sheet_data) if sheet_data else 0} entries from sheet")
            
            if not sheet_data:
                message = "No data found in sheets"
                logger.warning(message)
                sync_log.sync_status = "success"
                sync_log.sync_end_time = datetime.utcnow()
                sync_log.sync_error_message = message
                self.db.commit()
                return {"status": "success", "message": message, "processed": 0}

            processed = 0
            errors = []

            for entry in sheet_data:
                try:
                    # Log the entry being processed
                    logger.info(f"Processing entry: {entry}")
                    
                    processed_entry = {
                        'name': str(entry.get('Name', '')),
                        'age': int(float(entry.get('Age', 0))),
                        'gender': str(entry.get('Gender', '')),
                        'email': str(entry.get('Email', '')),
                        'phone': str(entry.get('Phone', '')),
                        'height': float(entry.get('Height (cm)', 0.0)),  # Updated
                        'weight': float(entry.get('Weight (kg)', 0.0)),  # Updated
                        'bmi': float(entry.get('BMI', 0.0)),
                        'lifestyle_score': int(float(entry.get('Lifestyle Score', 0))),
                        'medical_history': str(entry.get('Medical History', '')),
                        'lifestyle_factors': str(entry.get('Lifestyle Factors', '')),
                        'is_active': entry.get('Is Active', '').lower() == 'true'
                    }


                    # Calculate risk scores
                    insurance_risk = self.risk_calculator.calculate_insurance_risk(processed_entry)
                    diabetes_risk = self.risk_calculator.calculate_diabetes_risk(processed_entry)

                    # Create user data
                    user_data = models.UserData(
                        **processed_entry,
                        insurance_risk_score=insurance_risk,
                        diabetes_risk_score=diabetes_risk,
                        timestamp=datetime.utcnow()
                    )
                    
                    self.db.add(user_data)
                    self.db.commit()
                    logger.info(f"Successfully added user: {processed_entry['name']}")

                    processed += 1

                except Exception as e:
                    error_msg = f"Error processing entry: {str(e)}, Entry: {entry}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    self.db.rollback()
                    continue

            # Update sync log
            sync_log.sync_end_time = datetime.utcnow()
            sync_log.sync_status = "success" if not errors else "partial_success"
            sync_log.sync_error_message = str(errors) if errors else None
            self.db.commit()

            result = {
                "status": "success",
                "message": f"Processed {processed} entries",
                "processed": processed,
                "errors": errors if errors else None
            }
            logger.info(f"Sync completed: {result}")
            return result

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg)
            if sync_log:
                sync_log.sync_end_time = datetime.utcnow()
                sync_log.sync_status = "failure"
                sync_log.sync_error_message = error_msg
                self.db.commit()
            return {
                "status": "error",
                "message": error_msg,
                "processed": 0
            }
        
    def get_db_data(self) -> Dict[str, List[List[str]]]:
        """Get all data from database formatted for sheets"""
        try:
            # Get user data
            users = self.db.query(models.UserData).all()
            user_data = []
            for user in users:
                user_data.append([
                    user.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    user.name,
                    str(user.age),
                    user.gender,
                    user.email,
                    user.phone,
                    str(user.height),
                    str(user.weight),
                    str(user.bmi),
                    str(user.lifestyle_score),
                    str(user.insurance_risk_score),
                    str(user.diabetes_risk_score),
                    str(user.medical_history),
                    str(user.lifestyle_factors),
                    str(user.is_active),
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    user.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])

            # Get health activities
            activities = self.db.query(models.HealthActivity).all()
            health_data = []
            for activity in activities:
                health_data.append([
                    str(activity.id),
                    str(activity.user_id),
                    activity.activity_type,
                    activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    str(activity.duration),
                    str(activity.points_earned),
                    str(activity.details)
                ])

            # Get risk logs
            logs = self.db.query(models.RiskAssessmentLog).all()
            risk_data = []
            for log in logs:
                risk_data.append([
                    str(log.id),
                    str(log.user_id),
                    log.assessment_type,
                    log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    str(log.risk_score),
                    str(log.factors)
                ])

            return {
                'user_data': user_data,
                'health_activities': health_data,
                'risk_assessment_logs': risk_data
            }

        except Exception as e:
            logger.error(f"Error getting database data: {str(e)}")
            raise

    async def sync_to_sheets(self) -> Dict:
        """Sync data from database to Google Sheets"""
        try:
            # Create sync log
            sync_log = models.RiskAssessmentLog(
                assessment_type="db_to_sheets_sync",
                sync_start_time=datetime.utcnow(),
                sync_status="in_progress"
            )
            self.db.add(sync_log)
            self.db.commit()

            # Get all data from database
            db_data = self.get_db_data()

            # Update sheets
            self.sheets_client.update_sheets(db_data)

            # Update sync log
            sync_log.sync_end_time = datetime.utcnow()
            sync_log.sync_status = "success"
            self.db.commit()

            return {
                "status": "success",
                "message": "Data successfully synced to sheets",
                "records_synced": {
                    "user_data": len(db_data['user_data']),
                    "health_activities": len(db_data['health_activities']),
                    "risk_logs": len(db_data['risk_assessment_logs'])
                }
            }

        except Exception as e:
            if sync_log:
                sync_log.sync_end_time = datetime.utcnow()
                sync_log.sync_status = "failure"
                sync_log.sync_error_message = str(e)
                self.db.commit()
            
            logger.error(f"Error syncing to sheets: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "records_synced": 0
            }


    def sync_data(self, last_sync_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Main sync method that handles both directions of synchronization
        """
        try:
            # Update sync log
            sync_log = models.RiskAssessmentLog(
                assessment_type="synchronization",
                sync_start_time=datetime.now(),
                sync_status="in_progress"
            )
            self.db.add(sync_log)
            self.db.commit()

            try:
                # First sync from sheets to DB
                sheets_result = self.sync_from_sheets(last_sync_time)
                
                # Then sync from DB to sheets
                db_result = self.sync_to_sheets()

                # Update sync log with success
                sync_log.sync_end_time = datetime.now()
                sync_log.sync_status = "success"
                self.db.commit()

                return {
                    "status": "success",
                    "sheets_to_db": sheets_result,
                    "db_to_sheets": db_result
                }

            except Exception as e:
                # Update sync log with failure
                sync_log.sync_end_time = datetime.now()
                sync_log.sync_status = "failure"
                sync_log.sync_error_message = str(e)
                self.db.commit()
                raise

        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            raise

        