from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.safety_controller import (
    SafetyController
)

from app.services.dialing_coordinator import (
    DialingCoordinator
)


def test_agent_availability_drop_reduces_dialing():

    # ---------------------------------------------
    # STEP 1: Create predictive estimator
    # ---------------------------------------------

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )


    # ---------------------------------------------
    # STEP 2: Create safety controller
    #
    # Maximum allowed calls:
    #
    # available_agents × 2
    # ---------------------------------------------

    safety_controller = SafetyController(
        max_calls_per_available_agent=2,
        max_ringing_per_available_agent=100
    )


    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    # ---------------------------------------------
    # STEP 3: Initial situation
    #
    # 100 agents available
    # ---------------------------------------------

    initial_decision = coordinator.calculate(

        available_agents=100,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    # ---------------------------------------------
    # STEP 4: Sudden availability drop
    #
    # 40 agents disappear.
    #
    # Available:
    #
    # 100 → 60
    # ---------------------------------------------

    after_drop_decision = coordinator.calculate(

        available_agents=60,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    # ---------------------------------------------
    # STEP 5: Verify the system reacted
    # ---------------------------------------------

    # Predictive request should decrease because
    # fewer agents are available.

    assert (
        after_drop_decision.requested_calls
        < initial_decision.requested_calls
    )


    # Safety-approved calls should also decrease.

    assert (
        after_drop_decision.allowed_calls
        < initial_decision.allowed_calls
    )


    # ---------------------------------------------
    # STEP 6: Verify new capacity is respected
    # ---------------------------------------------

    assert (
        after_drop_decision.allowed_calls
        <= 60 * 2
    )


def test_agent_drop_blocks_new_calls_when_no_agents():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    safety_controller = SafetyController()

    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    # ---------------------------------------------
    # Before the drop
    # ---------------------------------------------

    before_drop = coordinator.calculate(

        available_agents=10,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    assert before_drop.allowed_calls > 0


    # ---------------------------------------------
    # All agents suddenly become unavailable
    # ---------------------------------------------

    after_drop = coordinator.calculate(

        available_agents=0,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    # ---------------------------------------------
    # No agents means no new dialing.
    # ---------------------------------------------

    assert after_drop.requested_calls == 0

    assert after_drop.allowed_calls == 0

    assert after_drop.safe is False