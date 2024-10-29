from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from datetime import datetime
from app.database import Base


class UserData(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Personal Information
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    
    # Health Metrics
    height = Column(Float)  # in cm
    weight = Column(Float)  # in kg
    bmi = Column(Float)
    lifestyle_score = Column(Float)
    
    # Risk Scores
    insurance_risk_score = Column(Float)
    diabetes_risk_score = Column(Float)
    
    # Additional Data
    medical_history = Column(JSON, nullable=True)
    lifestyle_factors = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthActivity(Base):
    __tablename__ = "health_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    activity_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Integer)  # in minutes
    points_earned = Column(Integer)
    details = Column(JSON, nullable=True)

class RiskAssessmentLog(Base):
    __tablename__ = "risk_assessment_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    assessment_type = Column(String)  
    timestamp = Column(DateTime, default=datetime.utcnow)
    risk_score = Column(Float)
    factors = Column(JSON)
    sync_start_time = Column(DateTime)
    sync_end_time = Column(DateTime)
    sync_status = Column(String)  # e.g., 'success', 'failure'
    sync_error_message = Column(String)