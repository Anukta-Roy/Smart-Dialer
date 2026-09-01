from app.database.database import SessionLocal

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState
from app.models.call import Call, CallState

from app.providers.provider_a import ProviderA
from app.providers.provider_b import ProviderB

from app.services.event_processor import (
    process_provider_event
)


def create_test_call(
    db,
    agent_name,
    phone_number,
    provider_name,
    provider_call_id
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
        provider_name=provider_name,
        provider_call_id=provider_call_id,
        state=CallState.INITIATED
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

    # Delete child record first because
    # Call references Agent and Borrower.
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


def test_provider_a_events_update_call():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        provider = ProviderA()

        provider_call_id = "provider_a_event_test"

        agent_id, borrower_id, call_id = (
            create_test_call(
                db=db,
                agent_name="Provider A Event Agent",
                phone_number="7777777771",
                provider_name=provider.get_provider_name(),
                provider_call_id=provider_call_id
            )
        )


        events = provider.get_call_events(
            provider_call_id
        )


        for event in events:

            updated_call = process_provider_event(
                db=db,
                event=event
            )


        assert (
            updated_call.state
            == CallState.COMPLETED
        )


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()


def test_provider_b_duplicate_and_stale_events():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        provider = ProviderB()

        provider_call_id = "provider_b_event_test"

        agent_id, borrower_id, call_id = (
            create_test_call(
                db=db,
                agent_name="Provider B Event Agent",
                phone_number="7777777772",
                provider_name=provider.get_provider_name(),
                provider_call_id=provider_call_id
            )
        )


        events = provider.get_call_events(
            provider_call_id
        )


        for event in events:

            updated_call = process_provider_event(
                db=db,
                event=event
            )


        # Despite duplicate and stale events,
        # the call must correctly finish.
        assert (
            updated_call.state
            == CallState.COMPLETED
        )


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()