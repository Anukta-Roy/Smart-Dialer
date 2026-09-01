from sqlalchemy.orm import Session

from app.models.call import Call, CallState


class InvalidCallStateTransition(Exception):
    pass


# Order of normal call progression.
# Higher number means the call has progressed further.
STATE_ORDER = {
    CallState.QUEUED: 0,
    CallState.RESERVED: 1,
    CallState.INITIATED: 2,
    CallState.RINGING: 3,
    CallState.ANSWERED: 4,
    CallState.CONNECTED: 5,
    CallState.COMPLETED: 6,
}


ALLOWED_TRANSITIONS = {

    CallState.QUEUED: [
        CallState.RESERVED,
        CallState.CANCELLED
    ],

    CallState.RESERVED: [
        CallState.INITIATED,
        CallState.CANCELLED,
        CallState.FAILED
    ],

    CallState.INITIATED: [
        CallState.RINGING,
        CallState.ANSWERED,
        CallState.FAILED,
        CallState.CANCELLED
    ],

    CallState.RINGING: [
        CallState.ANSWERED,
        CallState.FAILED,
        CallState.CANCELLED
    ],

    CallState.ANSWERED: [
        CallState.CONNECTED,
        CallState.COMPLETED,
        CallState.FAILED
    ],

    CallState.CONNECTED: [
        CallState.COMPLETED,
        CallState.FAILED
    ],

    CallState.COMPLETED: [],

    CallState.FAILED: [],

    CallState.CANCELLED: []
}


TERMINAL_STATES = {
    CallState.COMPLETED,
    CallState.FAILED,
    CallState.CANCELLED
}


def transition_call_state(
    db: Session,
    call_id: str,
    new_state: CallState
) -> Call:

    call = (
        db.query(Call)
        .filter(Call.id == call_id)
        .first()
    )

    if call is None:
        raise ValueError(
            f"Call {call_id} does not exist"
        )

    current_state = call.state


    # ------------------------------------------------
    # 1. Duplicate event
    # ------------------------------------------------
    # Example:
    # Current = RINGING
    # Incoming = RINGING
    #
    # Do nothing and return successfully.
    if current_state == new_state:
        return call


    # ------------------------------------------------
    # 2. Terminal state protection
    # ------------------------------------------------
    # Once a call is COMPLETED, FAILED, or CANCELLED,
    # no later provider event can change it.
    if current_state in TERMINAL_STATES:
        raise InvalidCallStateTransition(
            f"Call is already in terminal state "
            f"{current_state.value}"
        )


    # ------------------------------------------------
    # 3. Ignore stale/out-of-order events
    # ------------------------------------------------
    # Example:
    #
    # Current = ANSWERED
    # Incoming = RINGING
    #
    # RINGING happened earlier in the lifecycle,
    # so ignore it.
    if (
        current_state in STATE_ORDER
        and new_state in STATE_ORDER
        and STATE_ORDER[new_state] < STATE_ORDER[current_state]
    ):
        return call


    # ------------------------------------------------
    # 4. Validate normal transition
    # ------------------------------------------------
    allowed_states = ALLOWED_TRANSITIONS.get(
        current_state,
        []
    )

    if new_state not in allowed_states:

        raise InvalidCallStateTransition(
            f"Cannot transition call from "
            f"{current_state.value} to "
            f"{new_state.value}"
        )


    # ------------------------------------------------
    # 5. Apply transition
    # ------------------------------------------------
    call.state = new_state

    db.commit()

    db.refresh(call)

    return call