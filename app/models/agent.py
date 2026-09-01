from enum import Enum

from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum as SqlEnum

from app.database.database import Base


class AgentState(str, Enum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    DIALING = "DIALING"
    CONNECTED = "CONNECTED"
    WRAP_UP = "WRAP_UP"
    PAUSED = "PAUSED"


class Agent(Base):

    __tablename__ = "agents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    state = Column(
        SqlEnum(AgentState),
        nullable=False,
        default=AgentState.OFFLINE,
        index=True
    )