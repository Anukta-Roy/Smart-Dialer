from app.database.database import SessionLocal

from app.models.agent import Agent, AgentState
from app.models.borrower import Borrower, BorrowerState
from app.models.call import Call

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.safety_controller import (
    SafetyController
)

from app.services.dialing_coordinator import (
    DialingCoordinator
)

from app.services.progressive_dialer import (
    run_controlled_progressive_dialer
)


def test_predictive_pipeline_respects_safety_limit():

    db = SessionLocal()

    agent_ids = []
    borrower_ids = []

    try:

        # ---------------------------------
        # STEP 1: Create enough resources
        # ---------------------------------

        agents = [

            Agent(
                name=f"Integration Agent {i}",
                state=AgentState.AVAILABLE
            )

            for i in range(5)

        ]


        borrowers = [

            Borrower(
                phone_number=f"800000000{i}",
                state=BorrowerState.AVAILABLE
            )

            for i in range(20)

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


        # ---------------------------------
        # STEP 2: Create prediction model
        #
        # 10% answer rate means predictive
        # pacing will request many calls.
        # ---------------------------------

        estimator = AnswerRateEstimator(
            historical_answer_rate=0.10
        )


        # ---------------------------------
        # STEP 3: Safety limit
        #
        # Maximum:
        #
        # 5 available agents × 2
        # = 10 allowed calls
        # ---------------------------------

        safety_controller = SafetyController(
            max_calls_per_available_agent=2,
            max_ringing_per_available_agent=100
        )


        coordinator = DialingCoordinator(
            answer_rate_estimator=estimator,
            safety_controller=safety_controller
        )


        # ---------------------------------
        # STEP 4: Get predictive + safety
        # decision
        # ---------------------------------

        decision = coordinator.calculate(

            available_agents=5,

            connected_calls=0,

            ringing_calls=0,

            provider_health=1.0
        )


        # Predictive pacing wants:
        #
        # ceil(5 / 0.10)
        # = 50 calls

        assert (
            decision.requested_calls
            == 50
        )


        # Safety limits it to:
        #
        # 5 × 2
        # = 10 calls

        assert (
            decision.allowed_calls
            == 10
        )

        assert decision.safe is False


        # ---------------------------------
        # STEP 5: Pass ONLY safety-approved
        # calls to progressive dialer
        # ---------------------------------

        allocated_calls = (
            run_controlled_progressive_dialer(
                db=db,
                allowed_calls=decision.allowed_calls
            )
        )


        # ---------------------------------
        # STEP 6: Verify final allocation
        # ---------------------------------

        assert len(
            allocated_calls
        ) == 5


        # Although safety approved 10 calls,
        # only 5 can actually be allocated
        # because only 5 agents exist.

        assert len(
            allocated_calls
        ) <= decision.allowed_calls


        # ---------------------------------
        # STEP 7: Verify all test agents
        # were reserved
        # ---------------------------------

        for agent_id in agent_ids:

            agent = db.get(
                Agent,
                agent_id
            )

            assert (
                agent.state
                == AgentState.RESERVED
            )


        # ---------------------------------
        # STEP 8: Verify calls exist
        # ---------------------------------

        for call in allocated_calls:

            assert call.agent_id in agent_ids

            assert call.borrower_id in borrower_ids


    finally:

        db.rollback()


        # ---------------------------------
        # CLEANUP
        #
        # Delete only calls created using
        # this test's agents.
        # ---------------------------------

        if agent_ids:

            db.query(Call).filter(
                Call.agent_id.in_(agent_ids)
            ).delete(
                synchronize_session=False
            )


        if borrower_ids:

            db.query(Borrower).filter(
                Borrower.id.in_(borrower_ids)
            ).delete(
                synchronize_session=False
            )


        if agent_ids:

            db.query(Agent).filter(
                Agent.id.in_(agent_ids)
            ).delete(
                synchronize_session=False
            )


        db.commit()

        db.close()