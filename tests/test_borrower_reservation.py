from app.database.database import SessionLocal
from app.models.borrower import Borrower, BorrowerState

from app.services.reservation_service import reserve_borrower


def test_only_one_borrower_reservation():

    db = SessionLocal()

    borrower = Borrower(
        phone_number="9999999999",
        state=BorrowerState.AVAILABLE
    )

    db.add(borrower)

    db.commit()

    borrower_id = borrower.id

    first_attempt = reserve_borrower(
        db,
        borrower_id
    )

    second_attempt = reserve_borrower(
        db,
        borrower_id
    )

    assert first_attempt is True

    assert second_attempt is False

    db.delete(borrower)

    db.commit()

    db.close()