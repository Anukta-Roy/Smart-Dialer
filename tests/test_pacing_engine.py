import pytest

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.pacing_engine import (
    PacingInput,
    PredictivePacingEngine
)


def test_predictive_pacing_uses_historical_rate():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )

    pacing_input = PacingInput(
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = engine.calculate(
        pacing_input
    )


    # 10 / 0.50 = 20
    assert (
        decision.requested_calls
        == 20
    )

    assert (
        decision.predicted_answer_rate
        == 0.50
    )


def test_recent_outcomes_change_pacing():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50,
        historical_weight=0.3,
        recent_weight=0.7
    )


    # Recent behaviour:
    # 8 answers out of 10 = 80%

    outcomes = [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False
    ]

    for outcome in outcomes:

        estimator.record_outcome(
            outcome
        )


    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )


    pacing_input = PacingInput(
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = engine.calculate(
        pacing_input
    )


    # Predicted rate:
    #
    # 0.3 * 0.50
    # +
    # 0.7 * 0.80
    #
    # = 0.71
    #
    # ceil(10 / 0.71) = 15

    assert (
        decision.predicted_answer_rate
        == pytest.approx(0.71)
    )

    assert (
        decision.requested_calls
        == 15
    )


def test_ringing_calls_reduce_request():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )


    pacing_input = PacingInput(
        available_agents=10,
        connected_calls=0,
        ringing_calls=5,
        provider_health=1.0
    )


    decision = engine.calculate(
        pacing_input
    )


    # ceil(10 / 0.5) = 20
    # 20 - 5 ringing = 15

    assert (
        decision.requested_calls
        == 15
    )


def test_connected_calls_reduce_capacity():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )


    pacing_input = PacingInput(
        available_agents=10,
        connected_calls=4,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = engine.calculate(
        pacing_input
    )


    # Free capacity = 10 - 4 = 6
    # ceil(6 / 0.5) = 12

    assert (
        decision.free_agent_capacity
        == 6
    )

    assert (
        decision.requested_calls
        == 12
    )


def test_provider_health_reduces_request():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )


    pacing_input = PacingInput(
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=0.5
    )


    decision = engine.calculate(
        pacing_input
    )


    # Base = 20
    # Provider health = 50%
    # Result = 10

    assert (
        decision.requested_calls
        == 10
    )


def test_provider_outage_stops_pacing():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )


    pacing_input = PacingInput(
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=0.0
    )


    decision = engine.calculate(
        pacing_input
    )


    assert (
        decision.requested_calls
        == 0
    )


def test_no_agents_means_no_calls():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    engine = PredictivePacingEngine(
        answer_rate_estimator=estimator
    )


    pacing_input = PacingInput(
        available_agents=0,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = engine.calculate(
        pacing_input
    )


    assert (
        decision.requested_calls
        == 0
    )