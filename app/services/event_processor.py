from sqlalchemy.orm import Session

from app.models.call import Call
from app.providers.provider_event import ProviderEvent

from app.services.call_state_service import (
    transition_call_state
)


def process_provider_event(
    db: Session,
    event: ProviderEvent
) -> Call:
    """
    Process an event received from a telecom provider.

    Steps:
    1. Find the call using provider_call_id.
    2. Verify the event comes from the provider
       assigned to that call.
    3. Pass the new state to the call state machine.
    4. Let the state machine safely handle:
       - valid events
       - duplicate events
       - out-of-order events
    """

    # Find the call associated with this provider event
    call = (
        db.query(Call)
        .filter(
            Call.provider_call_id
            == event.provider_call_id
        )
        .first()
    )

    if call is None:
        raise ValueError(
            f"Call not found for provider call ID "
            f"{event.provider_call_id}"
        )


    # Verify the event is from the correct provider
    if call.provider_name != event.provider_name:

        raise ValueError(
            f"Provider mismatch. "
            f"Expected {call.provider_name}, "
            f"received {event.provider_name}"
        )


    # Process the state transition.
    #
    # transition_call_state already handles:
    # - duplicate events
    # - stale/out-of-order events
    # - invalid transitions
    updated_call = transition_call_state(
        db=db,
        call_id=call.id,
        new_state=event.call_state
    )

    return updated_call