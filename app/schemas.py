from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserDataBase(BaseModel):
    name: str
    age: int
    gender: str
    lifestyle_score: float

class UserDataCreate(UserDataBase):
    pass

class UserDataResponse(UserDataBase):
    id: int
    timestamp: datetime
    insurance_risk_score: float
    diabetes_risk_score: float

    class Config:
        orm_mode = True