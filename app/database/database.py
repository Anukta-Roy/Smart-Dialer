import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Load variable
load_dotenv()


# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for all database models
class Base(DeclarativeBase):
    pass


# Dependency for getting database sessions
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()