import pytest

from app.database.database import SessionLocal

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState
from app.models.call import Call, CallState
from app.services.progressive_dialer import (
    run_progressive_dialer
)
from app.services.call_allocator import (
    allocate_call,
    CallAllocationError
)


def test_allocate_call_success():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        # Create an available agent
        agent = Agent(
            name="Allocation Test Agent",
            state=AgentState.AVAILABLE
        )

        # Create an available borrower
        borrower = Borrower(
            phone_number="8888888888",
            state=BorrowerState.AVAILABLE
        )

        db.add(agent)
        db.add(borrower)

        db.commit()

        agent_id = agent.id
        borrower_id = borrower.id


        # Allocate the call
        call = allocate_call(
            db=db,
            agent_id=agent_id,
            borrower_id=borrower_id
        )

        call_id = call.id


        # Verify call was created
        assert call.state == CallState.RESERVED


        # Refresh objects from PostgreSQL
        db.refresh(agent)
        db.refresh(borrower)


        # Verify both resources were reserved
        assert agent.state == AgentState.RESERVED
        assert borrower.state == BorrowerState.RESERVED


    finally:

        # Delete Call first because it references
        # Agent and Borrower through foreign keys
        if call_id is not None:

            db.query(Call).filter(
                Call.id == call_id
            ).delete()


        # Delete Agent
        if agent_id is not None:

            db.query(Agent).filter(
                Agent.id == agent_id
            ).delete()


        # Delete Borrower
        if borrower_id is not None:

            db.query(Borrower).filter(
                Borrower.id == borrower_id
            ).delete()


        db.commit()

        db.close()


def test_allocation_rolls_back_when_borrower_unavailable():

    db = SessionLocal()

    agent_id = None
    borrower_id = None

    try:

        # Create an available agent
        agent = Agent(
            name="Rollback Test Agent",
            state=AgentState.AVAILABLE
        )

        # Create a borrower that is already reserved
        borrower = Borrower(
            phone_number="7777777777",
            state=BorrowerState.RESERVED
        )

        db.add(agent)
        db.add(borrower)

        db.commit()

        agent_id = agent.id
        borrower_id = borrower.id


        # Allocation should fail because the borrower
        # is not available
        with pytest.raises(CallAllocationError):

            allocate_call(
                db=db,
                agent_id=agent_id,
                borrower_id=borrower_id
            )


        # Reload agent state from PostgreSQL
        db.refresh(agent)


        # Agent reservation must have been rolled back
        assert agent.state == AgentState.AVAILABLE


    finally:

        # Delete any calls referencing this test agent
        if agent_id is not None:

            db.query(Call).filter(
                Call.agent_id == agent_id
            ).delete()


        # Delete any calls referencing this test borrower
        if borrower_id is not None:

            db.query(Call).filter(
                Call.borrower_id == borrower_id
            ).delete()


        # Delete Agent
        if agent_id is not None:

            db.query(Agent).filter(
                Agent.id == agent_id
            ).delete()


        # Delete Borrower
        if borrower_id is not None:

            db.query(Borrower).filter(
                Borrower.id == borrower_id
            ).delete()


        db.commit()

        db.close()


def test_progressive_dialer_respects_agent_capacity():

    db = SessionLocal()

    agent_ids = []
    borrower_ids = []
    call_ids = []

    try:

        # Create 2 available agents
        for i in range(2):

            agent = Agent(
                name=f"Progressive Agent {i}",
                state=AgentState.AVAILABLE
            )

            db.add(agent)

        # Create 5 available borrowers
        for i in range(5):

            borrower = Borrower(
                phone_number=f"900000000{i}",
                state=BorrowerState.AVAILABLE
            )

            db.add(borrower)

        db.commit()


        # Get IDs for cleanup
        agents = (
            db.query(Agent)
            .filter(
                Agent.name.like("Progressive Agent%")
            )
            .all()
        )

        borrowers = (
            db.query(Borrower)
            .filter(
                Borrower.phone_number.like("900000000%")
            )
            .all()
        )

        agent_ids = [agent.id for agent in agents]

        borrower_ids = [
            borrower.id
            for borrower in borrowers
        ]


        # Run Progressive Dialer
        calls = run_progressive_dialer(db)


        # Only 2 calls should be allocated
        # because only 2 agents exist
        assert len(calls) == 2


        call_ids = [
            call.id
            for call in calls
        ]


        # Both agents should be reserved
        reserved_agents = (
            db.query(Agent)
            .filter(
                Agent.id.in_(agent_ids),
                Agent.state == AgentState.RESERVED
            )
            .count()
        )

        assert reserved_agents == 2


        # Only 2 borrowers should be reserved
        reserved_borrowers = (
            db.query(Borrower)
            .filter(
                Borrower.id.in_(borrower_ids),
                Borrower.state == BorrowerState.RESERVED
            )
            .count()
        )

        assert reserved_borrowers == 2


        # Three borrowers should remain available
        available_borrowers = (
            db.query(Borrower)
            .filter(
                Borrower.id.in_(borrower_ids),
                Borrower.state == BorrowerState.AVAILABLE
            )
            .count()
        )

        assert available_borrowers == 3


    finally:

        # Delete calls first
        if call_ids:

            db.query(Call).filter(
                Call.id.in_(call_ids)
            ).delete(
                synchronize_session=False
            )


        # Delete test agents
        if agent_ids:

            db.query(Agent).filter(
                Agent.id.in_(agent_ids)
            ).delete(
                synchronize_session=False
            )


        # Delete test borrowers
        if borrower_ids:

            db.query(Borrower).filter(
                Borrower.id.in_(borrower_ids)
            ).delete(
                synchronize_session=False
            )


        db.commit()

        db.close()