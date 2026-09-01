import pytest

from app.database.database import SessionLocal

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState
from app.models.call import Call, CallState

from app.services.call_state_service import (
    transition_call_state,
    InvalidCallStateTransition
)


def create_test_call(
    db,
    agent_name,
    phone_number,
    call_state
):

    agent = Agent(
        name=agent_name,
        state=AgentState.AVAILABLE
    )

    borrower = Borrower(
        phone_number=phone_number,
        state=BorrowerState.AVAILABLE
    )

    db.add(agent)
    db.add(borrower)

    db.commit()

    call = Call(
        agent_id=agent.id,
        borrower_id=borrower.id,
        state=call_state
    )

    db.add(call)

    db.commit()

    return agent.id, borrower.id, call.id


def cleanup_test_data(
    db,
    agent_id,
    borrower_id,
    call_id
):

    if call_id is not None:

        db.query(Call).filter(
            Call.id == call_id
        ).delete()


    if agent_id is not None:

        db.query(Agent).filter(
            Agent.id == agent_id
        ).delete()


    if borrower_id is not None:

        db.query(Borrower).filter(
            Borrower.id == borrower_id
        ).delete()


    db.commit()


def test_valid_call_state_transition():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = create_test_call(
            db=db,
            agent_name="State Test Agent 1",
            phone_number="6666666661",
            call_state=CallState.RESERVED
        )


        updated_call = transition_call_state(
            db=db,
            call_id=call_id,
            new_state=CallState.INITIATED
        )


        assert updated_call.state == CallState.INITIATED


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()


def test_invalid_call_state_transition():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = create_test_call(
            db=db,
            agent_name="State Test Agent 2",
            phone_number="6666666662",
            call_state=CallState.COMPLETED
        )


        with pytest.raises(
            InvalidCallStateTransition
        ):

            transition_call_state(
                db=db,
                call_id=call_id,
                new_state=CallState.RINGING
            )


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()


def test_duplicate_event_is_ignored():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = create_test_call(
            db=db,
            agent_name="Duplicate Event Agent",
            phone_number="6666666663",
            call_state=CallState.RINGING
        )


        updated_call = transition_call_state(
            db=db,
            call_id=call_id,
            new_state=CallState.RINGING
        )


        assert updated_call.state == CallState.RINGING


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()


def test_out_of_order_event_is_ignored():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = create_test_call(
            db=db,
            agent_name="Out Of Order Agent",
            phone_number="6666666664",
            call_state=CallState.ANSWERED
        )


        updated_call = transition_call_state(
            db=db,
            call_id=call_id,
            new_state=CallState.RINGING
        )


        # Call must remain ANSWERED
        assert updated_call.state == CallState.ANSWERED


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()