import uuid
from enum import Enum

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy import Enum as SqlEnum

from app.database.database import Base


class CallState(str, Enum):
    QUEUED = "QUEUED"
    RESERVED = "RESERVED"
    INITIATED = "INITIATED"
    RINGING = "RINGING"
    ANSWERED = "ANSWERED"
    CONNECTED = "CONNECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Call(Base):

    __tablename__ = "calls"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    agent_id = Column(
        Integer,
        ForeignKey("agents.id"),
        nullable=True,
        index=True
    )

    borrower_id = Column(
        Integer,
        ForeignKey("borrowers.id"),
        nullable=False,
        index=True
    )

    provider_name = Column(
        String,
        nullable=True
    )

    provider_call_id = Column(
        String,
        nullable=True,
        unique=True
    )

    state = Column(
        SqlEnum(CallState),
        nullable=False,
        default=CallState.QUEUED,
        index=True
    )