import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import UserData, HealthActivity, RiskAssessmentLog

# Test database URL (use SQLite in-memory database for simplicity)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a new database session for the test
    db = TestingSessionLocal()
    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

# Override the get_db dependency
@pytest.fixture
def db_session(test_db):
    yield test_db
