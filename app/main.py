from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, APIRouter
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

load_dotenv()

from . import models
from . import schemas
from .database import engine, get_db
from .services.risk_calculator import RiskCalculator
from .services.sync_service import SyncService
from .services.google_sheets import GoogleSheetsClient



# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize risk calculator
risk_calculator = RiskCalculator()

app = FastAPI(
    title="Health Risk API",
    version="1.0.0",
    description="This API integrates user demographic and lifestyle data collected by a chatbot to assess health risks."
)

# Create routers for endpoints
default_router = APIRouter()
user_data_router = APIRouter()
sync_router = APIRouter()
risk_scores_router = APIRouter()

@default_router.get("/")
def read_root():
    return {
        "message": f"Welcome to {os.getenv('APP_NAME', 'Health Risk API')}",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# User Data Endpoints
@user_data_router.post("/", response_model=schemas.UserDataResponse, name="create_user_data")
def create_user_data(user_data: schemas.UserDataCreate, db: Session = Depends(get_db)):
    try:
        # Calculate risk scores
        insurance_risk = risk_calculator.calculate_insurance_risk(user_data.dict())
        diabetes_risk = risk_calculator.calculate_diabetes_risk(user_data.dict())

        # Create database model
        db_user = models.UserData(
            **user_data.dict(),
            insurance_risk_score=insurance_risk,
            diabetes_risk_score=diabetes_risk
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Construct the response object
        response_data = schemas.UserDataResponse.from_orm(db_user)
        return response_data

    except Exception as e:
        logger.error(f"Error creating user data: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user data: {str(e)}"
        )
    
    
@user_data_router.get("/", response_model=List[schemas.UserDataResponse], name="get_all_user_data")
def get_all_user_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        users = db.query(models.UserData).offset(skip).limit(limit).all()
        
        if not users: 
            return []
        
        user_data_responses = []
        for user in users:
            user_data_response = schemas.UserDataResponse.from_orm(user)
            user_data_responses.append(user_data_response)
        
        return user_data_responses
    except Exception as e:
        logger.error(f"Error retrieving user data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user data"
        )
# Async routes

@sync_router.get("/test_connection", response_model=Dict, name="test_sheets_connection")
async def test_sheets_connection():
    """Test the connection to Google Sheets"""
    try:
        sheets_client = GoogleSheetsClient()
        result = sheets_client.test_connection()
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "Successfully connected to Google Sheets",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Google Sheets: {result['message']}"
            )

    except Exception as e:
        logger.error(f"Error testing Google Sheets connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test Google Sheets connection: {str(e)}"
        )
    

@sync_router.post("/to_sheets", response_model=Dict, name="sync_db_to_sheets")
async def sync_db_to_sheets(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync data from database to Google Sheets"""
    try:
        sync_service = SyncService(db)
        background_tasks.add_task(sync_service.sync_to_sheets)

        return {
            "status": "success",
            "message": "Database to Google Sheets sync process started",
            "start_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error starting DB to Sheets sync process: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start sync process"
        )

@sync_router.post("/from_sheets", response_model=Dict, name="sync_sheets_to_db")
async def sync_sheets_to_db(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync data from Google Sheets to database"""
    try:
        # Get last successful sync timestamp
        last_sync = db.query(models.RiskAssessmentLog)\
            .filter(models.RiskAssessmentLog.sync_status == "success")\
            .order_by(models.RiskAssessmentLog.sync_end_time.desc())\
            .first()

        last_sync_time = last_sync.sync_end_time if last_sync else None

        sync_service = SyncService(db)
        
        # Execute sync immediately instead of background task for debugging
        result = await sync_service.sync_from_sheets(last_sync_time)
        
        # Log the result
        logger.info(f"Sync result: {result}")
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Sync failed: {result.get('message')}"
            )

        return {
            "status": "success",
            "message": result.get("message", "Sync completed"),
            "details": result,
            "start_time": datetime.now().isoformat(),
            "last_sync": last_sync_time.isoformat() if last_sync_time else None
        }

    except Exception as e:
        logger.error(f"Error in sync_sheets_to_db: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync: {str(e)}"
        )
    
@sync_router.get("/status", response_model=Dict, name="get_sync_status")
async def get_sync_status(db: Session = Depends(get_db)):
    """Get the status of the last sync operation"""
    try:
        last_sync = db.query(models.RiskAssessmentLog)\
            .order_by(models.RiskAssessmentLog.sync_start_time.desc())\
            .first()

        if not last_sync:
            return {
                "status": "no_sync",
                "message": "No sync operations found"
            }

        return {
            "status": last_sync.sync_status,
            "last_sync_type": last_sync.assessment_type,
            "start_time": last_sync.sync_start_time.isoformat() if last_sync.sync_start_time else None,
            "end_time": last_sync.sync_end_time.isoformat() if last_sync.sync_end_time else None,
            "error_message": last_sync.sync_error_message
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )
@user_data_router.delete("/", name="delete_all_users", status_code=204)
def delete_all_users(db: Session = Depends(get_db)):
    """Delete all user data from the database."""
    try:
        db.query(models.UserData).delete()
        db.commit()
        return {"message": "All users have been deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting all users: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete all users: {str(e)}"
        )

@sync_router.post("/", name="sync_all_data")
async def sync_all_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync data in both directions"""
    try:
        sync_service = SyncService(db)
        background_tasks.add_task(sync_service.sync_data)

        return {
            "status": "success",
            "message": "Sync process started",
            "start_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error starting sync process: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start sync process: {str(e)}"
        )
    
@risk_scores_router.post("/", response_model=schemas.RiskScoresResponse, name="get_risk_scores")
def get_risk_scores(user_data: schemas.UserDataCreate, db: Session = Depends(get_db)):
    try:
        # Calculate risk scores
        insurance_risk = risk_calculator.calculate_insurance_risk(user_data.dict())
        diabetes_risk = risk_calculator.calculate_diabetes_risk(user_data.dict())

        # Construct the response object
        response_data = schemas.RiskScoresResponse(
            insurance_risk_score=insurance_risk,
            diabetes_risk_score=diabetes_risk
        )

        return response_data
    except Exception as e:
        logger.error(f"Error calculating risk scores: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate risk scores"
        )
        


app.include_router(default_router, prefix="", tags=["Base Routes"]) 
app.include_router(user_data_router, prefix="/user", tags=["User Data"])
app.include_router(sync_router, prefix="/sync", tags=["Synchronization"])
app.include_router(risk_scores_router, prefix="/risk_scores", tags=["User risk scores"])
