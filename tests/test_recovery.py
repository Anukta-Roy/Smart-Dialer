import uuid

from app.database.database import SessionLocal

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState
from app.models.call import Call, CallState

from app.providers.base_provider import BaseProvider

from app.services.recovery_service import (
    initiate_call_with_fallback
)


# ----------------------------------------
# Test Provider: Always Fails
# ----------------------------------------

class AlwaysFailProvider(BaseProvider):

    def initiate_call(
        self,
        call_id: str,
        borrower_phone: str
    ) -> str:

        raise TimeoutError(
            "Simulated provider failure"
        )


    def cancel_call(
        self,
        provider_call_id: str
    ) -> bool:

        return True


    def get_provider_name(self) -> str:

        return "AlwaysFail"


    def get_call_events(
        self,
        provider_call_id: str
    ) -> list:

        return []


# ----------------------------------------
# Test Provider: Always Succeeds
# ----------------------------------------

class AlwaysSuccessProvider(BaseProvider):

    def initiate_call(
        self,
        call_id: str,
        borrower_phone: str
    ) -> str:

        return (
            f"success_provider_{uuid.uuid4()}"
        )


    def cancel_call(
        self,
        provider_call_id: str
    ) -> bool:

        return True


    def get_provider_name(self) -> str:

        return "AlwaysSuccess"


    def get_call_events(
        self,
        provider_call_id: str
    ) -> list:

        return []


# ----------------------------------------
# Test Provider: Counts Initiations
# ----------------------------------------

class CountingSuccessProvider(BaseProvider):

    def __init__(self):

        self.initiate_count = 0


    def initiate_call(
        self,
        call_id: str,
        borrower_phone: str
    ) -> str:

        self.initiate_count += 1

        return (
            f"counting_provider_"
            f"{uuid.uuid4()}"
        )


    def cancel_call(
        self,
        provider_call_id: str
    ) -> bool:

        return True


    def get_provider_name(self) -> str:

        return "CountingSuccess"


    def get_call_events(
        self,
        provider_call_id: str
    ) -> list:

        return []


# ----------------------------------------
# Helper: Create Test Call
# ----------------------------------------

def create_test_call(
    db,
    agent_name,
    phone_number
):

    agent = Agent(
        name=agent_name,
        state=AgentState.RESERVED
    )

    borrower = Borrower(
        phone_number=phone_number,
        state=BorrowerState.RESERVED
    )

    db.add(agent)
    db.add(borrower)

    db.commit()


    call = Call(
        agent_id=agent.id,
        borrower_id=borrower.id,
        state=CallState.RESERVED
    )

    db.add(call)

    db.commit()

    return (
        agent.id,
        borrower.id,
        call.id
    )


# ----------------------------------------
# Helper: Cleanup Test Data
# ----------------------------------------

def cleanup_test_data(
    db,
    agent_id,
    borrower_id,
    call_id
):

    # Delete Call first because it contains
    # foreign keys to Agent and Borrower.
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


# ----------------------------------------
# Test 1:
# Primary Fails -> Fallback Succeeds
# ----------------------------------------

def test_fallback_provider_is_used():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = (
            create_test_call(
                db=db,
                agent_name="Recovery Agent 1",
                phone_number="7777777781"
            )
        )


        updated_call = (
            initiate_call_with_fallback(
                db=db,
                call_id=call_id,
                borrower_phone="7777777781",
                primary_provider=AlwaysFailProvider(),
                fallback_provider=AlwaysSuccessProvider()
            )
        )


        assert (
            updated_call.state
            == CallState.INITIATED
        )

        assert (
            updated_call.provider_name
            == "AlwaysSuccess"
        )

        assert (
            updated_call.provider_call_id
            is not None
        )


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()


# ----------------------------------------
# Test 2:
# Both Providers Fail
# ----------------------------------------

def test_all_providers_fail():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = (
            create_test_call(
                db=db,
                agent_name="Recovery Agent 2",
                phone_number="7777777782"
            )
        )


        updated_call = (
            initiate_call_with_fallback(
                db=db,
                call_id=call_id,
                borrower_phone="7777777782",
                primary_provider=AlwaysFailProvider(),
                fallback_provider=AlwaysFailProvider()
            )
        )


        assert (
            updated_call.state
            == CallState.FAILED
        )


        agent = (
            db.query(Agent)
            .filter(
                Agent.id == agent_id
            )
            .first()
        )

        borrower = (
            db.query(Borrower)
            .filter(
                Borrower.id == borrower_id
            )
            .first()
        )


        assert (
            agent.state
            == AgentState.AVAILABLE
        )

        assert (
            borrower.state
            == BorrowerState.AVAILABLE
        )


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()


# ----------------------------------------
# Test 3:
# Retry Must Not Create Duplicate Call
# ----------------------------------------

def test_retry_does_not_initiate_duplicate_call():

    db = SessionLocal()

    agent_id = None
    borrower_id = None
    call_id = None

    try:

        agent_id, borrower_id, call_id = (
            create_test_call(
                db=db,
                agent_name="Recovery Agent 3",
                phone_number="7777777783"
            )
        )


        provider = CountingSuccessProvider()

        fallback_provider = (
            AlwaysFailProvider()
        )


        # --------------------------------
        # First initiation attempt
        # --------------------------------

        first_call = (
            initiate_call_with_fallback(
                db=db,
                call_id=call_id,
                borrower_phone="7777777783",
                primary_provider=provider,
                fallback_provider=fallback_provider
            )
        )


        first_provider_call_id = (
            first_call.provider_call_id
        )


        # --------------------------------
        # Retry the SAME database call
        # --------------------------------

        second_call = (
            initiate_call_with_fallback(
                db=db,
                call_id=call_id,
                borrower_phone="7777777783",
                primary_provider=provider,
                fallback_provider=fallback_provider
            )
        )


        # Provider must only be initiated once.
        assert provider.initiate_count == 1


        # Retry must retain the same provider call ID.
        assert (
            second_call.provider_call_id
            == first_provider_call_id
        )


        # Retry must still refer to the same Call record.
        assert (
            second_call.id
            == call_id
        )


    finally:

        cleanup_test_data(
            db,
            agent_id,
            borrower_id,
            call_id
        )

        db.close()