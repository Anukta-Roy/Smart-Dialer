from fastapi import FastAPI

from app.database.database import Base, engine

# Import all models so SQLAlchemy knows about them
from app.models.agent import Agent
from app.models.borrower import Borrower
from app.models.call import Call
from app.models.provider_event import ProviderEvent


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SmartDialer"
)


@app.get("/")
def health():
    return {
        "status": "running"
    }