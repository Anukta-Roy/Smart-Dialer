from sqlalchemy.orm import Session

from app.models.call import Call, CallState
from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState

from app.providers.base_provider import BaseProvider


def initiate_call_with_fallback(
    db: Session,
    call_id: str,
    borrower_phone: str,
    primary_provider: BaseProvider,
    fallback_provider: BaseProvider
) -> Call:
    """
    Try the primary provider first.

    If it fails, try the fallback provider.

    The same database Call record is reused so
    retries cannot create duplicate calls.
    """

    call = (
        db.query(Call)
        .filter(Call.id == call_id)
        .first()
    )

    if call is None:
        raise ValueError(
            f"Call {call_id} does not exist"
        )

    # ---------------------------------------------
    # Idempotency protection
    # ---------------------------------------------
    # If the call was already successfully initiated,
    # do not initiate another provider call.

    if call.provider_call_id is not None:

        return call


    providers = [
        primary_provider,
        fallback_provider
    ]


    for provider in providers:

        try:

            provider_call_id = (
                provider.initiate_call(
                    call_id=call.id,
                    borrower_phone=borrower_phone
                )
            )


            # Store provider details on the SAME call.

            call.provider_name = (
                provider.get_provider_name()
            )

            call.provider_call_id = (
                provider_call_id
            )

            call.state = CallState.INITIATED

            db.commit()

            db.refresh(call)

            return call


        except TimeoutError:

            # Provider failed.
            # Try the next provider.

            continue


    # ---------------------------------------------
    # Both providers failed
    # ---------------------------------------------

    call.state = CallState.FAILED


    # Release resources because no call was initiated.

    agent = (
        db.query(Agent)
        .filter(
            Agent.id == call.agent_id
        )
        .first()
    )

    borrower = (
        db.query(Borrower)
        .filter(
            Borrower.id == call.borrower_id
        )
        .first()
    )


    if agent is not None:

        agent.state = AgentState.AVAILABLE


    if borrower is not None:

        borrower.state = BorrowerState.AVAILABLE


    db.commit()

    db.refresh(call)

    return call


# =================================================
# WORKER CRASH RECOVERY
# =================================================

def recover_stuck_calls(
    db: Session
) -> list[Call]:
    """
    Recover calls that may have been left incomplete
    after a worker crash or application restart.

    Calls in RESERVED or INITIATED state are considered
    incomplete for this basic recovery implementation.

    Recovery:
    - marks the call as FAILED
    - releases the agent
    - releases the borrower

    Row locks are used so concurrent recovery workers
    cannot recover the same call simultaneously.
    """

    # Find calls that may have been left incomplete.

    stuck_calls = (
        db.query(Call)
        .filter(
            Call.state.in_(
                [
                    CallState.RESERVED,
                    CallState.INITIATED
                ]
            )
        )
        .all()
    )


    recovered_calls = []


    try:

        for call in stuck_calls:

            # Lock the call row.

            locked_call = (
                db.query(Call)
                .filter(
                    Call.id == call.id
                )
                .with_for_update()
                .first()
            )


            if locked_call is None:

                continue


            # Another worker may have already changed
            # the call while we waited for the lock.

            if locked_call.state not in (
                CallState.RESERVED,
                CallState.INITIATED
            ):

                continue


            # Mark the incomplete call as failed.

            locked_call.state = CallState.FAILED


            # -----------------------------------------
            # Release the agent
            # -----------------------------------------

            if locked_call.agent_id is not None:

                agent = (
                    db.query(Agent)
                    .filter(
                        Agent.id
                        == locked_call.agent_id
                    )
                    .with_for_update()
                    .first()
                )


                if agent is not None:

                    agent.state = (
                        AgentState.AVAILABLE
                    )


            # -----------------------------------------
            # Release the borrower
            # -----------------------------------------

            borrower = (
                db.query(Borrower)
                .filter(
                    Borrower.id
                    == locked_call.borrower_id
                )
                .with_for_update()
                .first()
            )


            if borrower is not None:

                borrower.state = (
                    BorrowerState.AVAILABLE
                )


            recovered_calls.append(
                locked_call
            )


        # Commit all recoveries as one transaction.

        db.commit()


        # Refresh recovered objects so their final
        # committed database state is returned.

        for call in recovered_calls:

            db.refresh(call)


    except Exception:

        db.rollback()

        raise


    return recovered_calls