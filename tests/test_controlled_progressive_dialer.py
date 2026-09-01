from app.database.database import SessionLocal

from app.models.agent import (
    Agent,
    AgentState
)

from app.models.borrower import (
    Borrower,
    BorrowerState
)

from app.models.call import Call

from app.services.progressive_dialer import (
    run_controlled_progressive_dialer
)


def test_controlled_dialer_respects_allowed_calls():

    db = SessionLocal()

    agent_ids = []
    borrower_ids = []

    try:

        agents = [

            Agent(
                name=f"Controlled Agent {i}",
                state=AgentState.AVAILABLE
            )

            for i in range(5)

        ]


        borrowers = [

            Borrower(
                phone_number=f"700000000{i}",
                state=BorrowerState.AVAILABLE
            )

            for i in range(5)

        ]


        db.add_all(agents)
        db.add_all(borrowers)

        db.commit()


        agent_ids = [
            agent.id
            for agent in agents
        ]

        borrower_ids = [
            borrower.id
            for borrower in borrowers
        ]


        allocated_calls = (
            run_controlled_progressive_dialer(
                db=db,
                allowed_calls=2
            )
        )


        assert len(allocated_calls) == 2


    finally:

        db.rollback()

        # Delete only calls created using
        # this test's agents.

        if agent_ids:

            db.query(Call).filter(
                Call.agent_id.in_(agent_ids)
            ).delete(
                synchronize_session=False
            )


        # Delete only borrowers created
        # by this test.

        if borrower_ids:

            db.query(Borrower).filter(
                Borrower.id.in_(borrower_ids)
            ).delete(
                synchronize_session=False
            )


        # Delete only agents created
        # by this test.

        if agent_ids:

            db.query(Agent).filter(
                Agent.id.in_(agent_ids)
            ).delete(
                synchronize_session=False
            )


        db.commit()
        db.close()


def test_controlled_dialer_stops_when_no_resources():

    db = SessionLocal()

    agent_id = None
    borrower_id = None

    try:

        agent = Agent(
            name="Single Controlled Agent",
            state=AgentState.AVAILABLE
        )

        borrower = Borrower(
            phone_number="7111111111",
            state=BorrowerState.AVAILABLE
        )


        db.add(agent)
        db.add(borrower)

        db.commit()


        agent_id = agent.id
        borrower_id = borrower.id


        allocated_calls = (
            run_controlled_progressive_dialer(
                db=db,
                allowed_calls=5
            )
        )


        # Only one agent and one borrower
        # were created by this test.

        assert len(allocated_calls) == 1


    finally:

        db.rollback()


        # Delete calls for this test agent.

        if agent_id is not None:

            db.query(Call).filter(
                Call.agent_id == agent_id
            ).delete(
                synchronize_session=False
            )


        if borrower_id is not None:

            db.query(Borrower).filter(
                Borrower.id == borrower_id
            ).delete(
                synchronize_session=False
            )


        if agent_id is not None:

            db.query(Agent).filter(
                Agent.id == agent_id
            ).delete(
                synchronize_session=False
            )


        db.commit()
        db.close()


def test_zero_allowed_calls_creates_nothing():

    db = SessionLocal()

    agent_id = None
    borrower_id = None

    try:

        agent = Agent(
            name="Zero Limit Agent",
            state=AgentState.AVAILABLE
        )

        borrower = Borrower(
            phone_number="7222222222",
            state=BorrowerState.AVAILABLE
        )


        db.add(agent)
        db.add(borrower)

        db.commit()


        agent_id = agent.id
        borrower_id = borrower.id


        allocated_calls = (
            run_controlled_progressive_dialer(
                db=db,
                allowed_calls=0
            )
        )


        assert len(allocated_calls) == 0


    finally:

        db.rollback()


        # There should be no call, but delete
        # defensively if one somehow exists.

        if agent_id is not None:

            db.query(Call).filter(
                Call.agent_id == agent_id
            ).delete(
                synchronize_session=False
            )


        if borrower_id is not None:

            db.query(Borrower).filter(
                Borrower.id == borrower_id
            ).delete(
                synchronize_session=False
            )


        if agent_id is not None:

            db.query(Agent).filter(
                Agent.id == agent_id
            ).delete(
                synchronize_session=False
            )


        db.commit()
        db.close()