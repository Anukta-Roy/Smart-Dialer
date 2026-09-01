from sqlalchemy.orm import Session

from app.models.call import Call, CallState

from app.services.reservation_service import (
    reserve_agent,
    reserve_borrower
)


class CallAllocationError(Exception):
    pass


def allocate_call(
    db: Session,
    agent_id: int,
    borrower_id: int
) -> Call:

    try:

        # Reserve agent without committing
        agent_reserved = reserve_agent(
            db=db,
            agent_id=agent_id,
            commit=False
        )

        if not agent_reserved:
            raise CallAllocationError(
                f"Agent {agent_id} is not available"
            )


        # Reserve borrower without committing
        borrower_reserved = reserve_borrower(
            db=db,
            borrower_id=borrower_id,
            commit=False
        )

        if not borrower_reserved:
            raise CallAllocationError(
                f"Borrower {borrower_id} is not available"
            )


        # Create call record
        call = Call(
            agent_id=agent_id,
            borrower_id=borrower_id,
            state=CallState.RESERVED
        )

        db.add(call)


        # Commit EVERYTHING together
        db.commit()


        # Refresh to get generated values
        db.refresh(call)


        return call


    except Exception:

        # Undo ALL changes
        db.rollback()

        raise