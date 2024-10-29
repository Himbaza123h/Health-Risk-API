from app.database import init_db
from app.models import Base, UserData, HealthActivity, RiskAssessmentLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init():
    logger.info("Creating initial database...")
    init_db()
    logger.info("Database initialization completed!")

if __name__ == "__main__":
    init()