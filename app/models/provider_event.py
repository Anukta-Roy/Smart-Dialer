import uuid

from sqlalchemy import Column, String, Integer, ForeignKey

from app.database.database import Base


class ProviderEvent(Base):

    __tablename__ = "provider_events"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    provider_event_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    call_id = Column(
        String,
        ForeignKey("calls.id"),
        nullable=False,
        index=True
    )

    event_type = Column(
        String,
        nullable=False
    )