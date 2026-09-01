from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.safety_controller import (
    SafetyController
)

from app.services.dialing_coordinator import (
    DialingCoordinator
)


def test_predictive_request_passes_through_safety():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )


    safety_controller = SafetyController(
        max_calls_per_available_agent=2,
        max_ringing_per_available_agent=10
    )


    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    decision = coordinator.calculate(

        available_agents=10,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    # Predictive pacing:
    #
    # 10 free agents
    # 50% predicted answer rate
    #
    # ceil(10 / 0.5)
    # = 20 requested calls

    assert (
        decision.requested_calls
        == 20
    )


    # Safety allows maximum:
    #
    # 10 agents * 2 calls
    # = 20

    assert (
        decision.allowed_calls
        == 20
    )

    assert decision.safe is True


def test_safety_can_reduce_predictive_request():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.10
    )


    safety_controller = SafetyController(
        max_calls_per_available_agent=2,
        max_ringing_per_available_agent=100
    )


    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    decision = coordinator.calculate(

        available_agents=10,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    # Predictive engine wants:
    #
    # ceil(10 / 0.10)
    # = 100 calls

    assert (
        decision.requested_calls
        == 100
    )


    # Safety limit:
    #
    # 10 * 2
    # = 20

    assert (
        decision.allowed_calls
        == 20
    )

    assert decision.safe is False


def test_recent_campaign_behavior_changes_final_decision():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.70,
        historical_weight=0.3,
        recent_weight=0.7
    )


    # Recent campaign suddenly performs poorly.
    #
    # 1 answer out of 10 calls.

    outcomes = [

        True,

        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False
    ]


    for outcome in outcomes:

        estimator.record_outcome(
            outcome
        )


    safety_controller = SafetyController(
        max_calls_per_available_agent=2,
        max_ringing_per_available_agent=100
    )


    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    decision = coordinator.calculate(

        available_agents=10,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    # Predicted answer rate:
    #
    # 0.3 * 0.70
    # +
    # 0.7 * 0.10
    #
    # = 0.28

    assert (
        decision.predicted_answer_rate
        > 0.27
    )

    assert (
        decision.predicted_answer_rate
        < 0.29
    )


    # The predictive engine may request
    # more calls due to the answer-rate drop.

    assert (
        decision.requested_calls
        > decision.allowed_calls
    )


    # But safety must independently
    # cap the request.

    assert (
        decision.allowed_calls
        == 20
    )

    assert decision.safe is False


def test_provider_failure_blocks_final_dialing():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )


    safety_controller = SafetyController()


    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    decision = coordinator.calculate(

        available_agents=10,

        connected_calls=0,

        ringing_calls=0,

        provider_health=0.0
    )


    assert (
        decision.requested_calls
        == 0
    )

    assert (
        decision.allowed_calls
        == 0
    )

    assert decision.safe is False


def test_no_agents_means_no_final_calls():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )


    safety_controller = SafetyController()


    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    decision = coordinator.calculate(

        available_agents=0,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    assert (
        decision.requested_calls
        == 0
    )

    assert (
        decision.allowed_calls
        == 0
    )