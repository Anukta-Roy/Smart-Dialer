from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState


def reserve_agent(
    db: Session,
    agent_id: int,
    commit: bool = True
) -> bool:

    statement = (
        update(Agent)
        .where(
            Agent.id == agent_id,
            Agent.state == AgentState.AVAILABLE
        )
        .values(
            state=AgentState.RESERVED
        )
    )

    result = db.execute(statement)

    if result.rowcount != 1:
        return False

    if commit:
        db.commit()

    return True


def release_agent(
    db: Session,
    agent_id: int,
    commit: bool = True
) -> bool:

    statement = (
        update(Agent)
        .where(
            Agent.id == agent_id,
            Agent.state == AgentState.RESERVED
        )
        .values(
            state=AgentState.AVAILABLE
        )
    )

    result = db.execute(statement)

    if result.rowcount != 1:
        return False

    if commit:
        db.commit()

    return True


def reserve_borrower(
    db: Session,
    borrower_id: int,
    commit: bool = True
) -> bool:

    statement = (
        update(Borrower)
        .where(
            Borrower.id == borrower_id,
            Borrower.state == BorrowerState.AVAILABLE
        )
        .values(
            state=BorrowerState.RESERVED
        )
    )

    result = db.execute(statement)

    if result.rowcount != 1:
        return False

    if commit:
        db.commit()

    return True


def release_borrower(
    db: Session,
    borrower_id: int,
    commit: bool = True
) -> bool:

    statement = (
        update(Borrower)
        .where(
            Borrower.id == borrower_id,
            Borrower.state == BorrowerState.RESERVED
        )
        .values(
            state=BorrowerState.AVAILABLE
        )
    )

    result = db.execute(statement)

    if result.rowcount != 1:
        return False

    if commit:
        db.commit()

    return True