import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app 
from app import models

# Test database URL for in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_db():
    # Create an engine for the test database
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create a new database session
    db = TestingSessionLocal()
    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    yield test_db

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client



# Test calculating risk scores
def test_get_risk_scores(client):
    user_data = {
        "name": "Alain Honore",
        "age": 30,
        "gender": "male",
        "email": "himbazaalain022@gmail.com",
        "phone": "0782179022",
        "height": 180.5,
        "weight": 75.0,
        "lifestyle_score": 85.0,
        "medical_history": {"conditions": ["none"]},
        "lifestyle_factors": {"exercise": "daily"},
    }

    response = client.post("/risk_scores/", json=user_data)
    
    assert response.status_code == 200
    response_data = response.json()
    assert "insurance_risk_score" in response_data
    assert "diabetes_risk_score" in response_data
