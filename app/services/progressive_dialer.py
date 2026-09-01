from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState
from app.models.call import Call

from app.services.call_allocator import (
    allocate_call,
    CallAllocationError
)


def run_progressive_dialer(
    db: Session
) -> list[Call]:
    """
    Original progressive dialer.

    Allocates calls until there are no more available
    agents or borrowers.
    """

    allocated_calls = []

    while True:

        # Find one available agent
        agent = (
            db.query(Agent)
            .filter(
                Agent.state == AgentState.AVAILABLE
            )
            .order_by(Agent.id)
            .first()
        )

        # Find one available borrower
        borrower = (
            db.query(Borrower)
            .filter(
                Borrower.state == BorrowerState.AVAILABLE
            )
            .order_by(Borrower.id)
            .first()
        )

        # Stop if either resource is unavailable
        if agent is None or borrower is None:
            break

        try:

            # Allocate agent and borrower atomically
            call = allocate_call(
                db=db,
                agent_id=agent.id,
                borrower_id=borrower.id
            )

            allocated_calls.append(call)

        except CallAllocationError:

            # Another worker may have reserved the
            # agent or borrower concurrently.
            db.rollback()
            continue

    return allocated_calls


def run_controlled_progressive_dialer(
    db: Session,
    allowed_calls: int
) -> list[Call]:
    """
    Controlled progressive dialer.

    Only attempts to allocate the number of calls
    approved by the Safety Controller.

    The allowed_calls value must come from the
    controlled Predictive Pacing -> Safety pipeline.

    Atomic allocation is still handled by
    allocate_call().
    """

    allocated_calls = []

    # Safety boundary:
    # never allocate a negative or zero number of calls.
    if allowed_calls <= 0:
        return allocated_calls

    while len(allocated_calls) < allowed_calls:

        # Find one currently available agent
        agent = (
            db.query(Agent)
            .filter(
                Agent.state == AgentState.AVAILABLE
            )
            .order_by(Agent.id)
            .first()
        )

        # Find one currently available borrower
        borrower = (
            db.query(Borrower)
            .filter(
                Borrower.state == BorrowerState.AVAILABLE
            )
            .order_by(Borrower.id)
            .first()
        )

        # Resources disappeared or no more resources exist.
        if agent is None or borrower is None:
            break

        try:

            # Atomic transaction:
            #
            # - reserve agent
            # - reserve borrower
            # - create call
            #
            # If allocation fails, allocate_call()
            # must roll back the transaction.

            call = allocate_call(
                db=db,
                agent_id=agent.id,
                borrower_id=borrower.id
            )

            allocated_calls.append(call)

        except CallAllocationError:

            # Another concurrent worker may have
            # reserved the selected resource.
            db.rollback()

            # Continue searching for another available
            # agent/borrower.
            continue

    return allocated_calls