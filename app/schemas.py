from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

class MedicalHistory(BaseModel):
    conditions: List[str] = []
    medications: List[str] = []

class LifestyleFactors(BaseModel):
    exercise: Optional[str] = None
    diet: Optional[str] = None

class UserDataBase(BaseModel):
    name: str
    age: int
    gender: str
    email: EmailStr
    phone: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    lifestyle_score: float
    medical_history: Optional[MedicalHistory] = None
    lifestyle_factors: Optional[LifestyleFactors] = None
    is_active: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserDataCreate(UserDataBase):
    pass

class UserDataResponse(UserDataBase):
    id: int
    insurance_risk_score: float
    diabetes_risk_score: float

    class Config:
        orm_mode = True

class RiskScoresResponse(BaseModel):
    insurance_risk_score: float
    diabetes_risk_score: float

    class Config:
        orm_mode = True