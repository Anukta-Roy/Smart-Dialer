from app.database.database import SessionLocal

from app.models.agent import (
    Agent,
    AgentState
)

from app.models.borrower import (
    Borrower,
    BorrowerState
)

from app.models.call import (
    Call,
    CallState
)

from app.services.call_allocator import (
    allocate_call
)

from app.services.recovery_service import (
    recover_stuck_calls
)


def test_worker_crash_recovers_reserved_call():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        # ---------------------------------
        # STEP 1: Create available resources
        # ---------------------------------

        agent = Agent(
            name="Crash Recovery Agent",
            state=AgentState.AVAILABLE
        )

        borrower = Borrower(
            phone_number="7333333333",
            state=BorrowerState.AVAILABLE
        )

        db.add(agent)
        db.add(borrower)

        db.commit()

        agent_id = agent.id
        borrower_id = borrower.id


        # ---------------------------------
        # STEP 2: Allocate call
        # ---------------------------------

        call = allocate_call(
            db=db,
            agent_id=agent_id,
            borrower_id=borrower_id
        )

        call_id = call.id


        # Allocation should reserve both.

        db.refresh(agent)
        db.refresh(borrower)

        assert call.state == CallState.RESERVED

        assert (
            agent.state
            == AgentState.RESERVED
        )

        assert (
            borrower.state
            == BorrowerState.RESERVED
        )


        # ---------------------------------
        # STEP 3: Simulate worker crash
        #
        # We intentionally do NOT:
        #
        # - complete the call
        # - release the agent
        # - release the borrower
        #
        # The database is left in the state
        # a crashed worker could leave behind.
        # ---------------------------------


        # ---------------------------------
        # STEP 4: Simulate application restart
        #
        # Close current session and create
        # a new database session.
        # ---------------------------------

        db.close()

        recovery_db = SessionLocal()


        # ---------------------------------
        # STEP 5: Run recovery
        # ---------------------------------

        recovered_calls = (
            recover_stuck_calls(
                recovery_db
            )
        )


        assert len(recovered_calls) >= 1


        # ---------------------------------
        # STEP 6: Verify the specific call
        # was recovered.
        # ---------------------------------

        recovered_call = (
            recovery_db.query(Call)
            .filter(
                Call.id == call_id
            )
            .first()
        )

        assert (
            recovered_call.state
            == CallState.FAILED
        )


        # ---------------------------------
        # STEP 7: Verify resources released
        # ---------------------------------

        recovered_agent = (
            recovery_db.query(Agent)
            .filter(
                Agent.id == agent_id
            )
            .first()
        )

        recovered_borrower = (
            recovery_db.query(Borrower)
            .filter(
                Borrower.id == borrower_id
            )
            .first()
        )


        assert (
            recovered_agent.state
            == AgentState.AVAILABLE
        )

        assert (
            recovered_borrower.state
            == BorrowerState.AVAILABLE
        )


        recovery_db.close()


    finally:

        # Open a clean session for cleanup.

        cleanup_db = SessionLocal()

        try:

            if call_id is not None:

                cleanup_db.query(Call).filter(
                    Call.id == call_id
                ).delete(
                    synchronize_session=False
                )


            if borrower_id is not None:

                cleanup_db.query(Borrower).filter(
                    Borrower.id == borrower_id
                ).delete(
                    synchronize_session=False
                )


            if agent_id is not None:

                cleanup_db.query(Agent).filter(
                    Agent.id == agent_id
                ).delete(
                    synchronize_session=False
                )


            cleanup_db.commit()

        finally:

            cleanup_db.close()