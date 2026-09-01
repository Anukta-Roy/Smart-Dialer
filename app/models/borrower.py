from enum import Enum

from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum as SqlEnum

from app.database.database import Base


class BorrowerState(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    COMPLETED = "COMPLETED"


class Borrower(Base):

    __tablename__ = "borrowers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    phone_number = Column(
        String,
        unique=True,
        nullable=False
    )

    state = Column(
        SqlEnum(BorrowerState),
        nullable=False,
        default=BorrowerState.AVAILABLE,
        index=True
    )