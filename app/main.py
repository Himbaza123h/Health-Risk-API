# app/main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

from . import models
from . import schemas
from .database import engine, get_db
from .services.risk_calculator import RiskCalculator
from .services.google_sheets import GoogleSheetsClient
from .services.sync_service import SyncService

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
    title=os.getenv("APP_NAME", "Health Risk API"),
    version=os.getenv("APP_VERSION", "1.0.0")
)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {os.getenv('APP_NAME', 'Health Risk API')}",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/user-data/", response_model=schemas.UserDataResponse)
def create_user_data(user_data: schemas.UserDataCreate, db: Session = Depends(get_db)):
    try:
        # Convert Pydantic model to dict
        user_dict = user_data.dict()
        
        # Calculate risk scores
        insurance_risk = risk_calculator.calculate_insurance_risk(user_dict)
        diabetes_risk = risk_calculator.calculate_diabetes_risk(user_dict)
        
        # Create database model
        db_user = models.UserData(
            **user_dict,
            insurance_risk_score=insurance_risk,
            diabetes_risk_score=diabetes_risk
        )
        
        # Add and commit to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
        
    except Exception as e:
        logger.error(f"Error creating user data: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create user data"
        )

@app.get("/user-data/", response_model=List[schemas.UserDataResponse])
def get_all_user_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        users = db.query(models.UserData).offset(skip).limit(limit).all()
        return users
    except Exception as e:
        logger.error(f"Error retrieving user data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user data"
        )

@app.post("/sync/")
async def sync_sheets_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint to trigger Google Sheets synchronization
    """
    try:
        # Get last successful sync timestamp
        last_sync = db.query(models.RiskAssessmentLog)\
            .order_by(models.RiskAssessmentLog.timestamp.desc())\
            .first()
        
        last_sync_time = last_sync.timestamp if last_sync else None
        
        # Initialize sync service
        sync_service = SyncService(db)
        
        # Add sync task to background tasks
        background_tasks.add_task(sync_service.sync_data, last_sync_time)
        
        return {
            "status": "success",
            "message": "Sync process started",
            "last_sync": last_sync_time
        }
        
    except Exception as e:
        logger.error(f"Error starting sync process: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start sync process"
        )

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}