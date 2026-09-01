import pytest

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)


def test_uses_historical_rate_without_recent_data():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )


    predicted_rate = (
        estimator.predict_answer_rate()
    )


    assert predicted_rate == 0.50


def test_recent_data_changes_prediction():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50,
        historical_weight=0.3,
        recent_weight=0.7
    )


    # 4 answered out of 5.
    for outcome in [
        True,
        True,
        True,
        False,
        True
    ]:

        estimator.record_outcome(
            outcome
        )


    predicted_rate = (
        estimator.predict_answer_rate()
    )


    # Historical contribution:
    # 0.3 * 0.50 = 0.15
    #
    # Recent contribution:
    # 0.7 * 0.80 = 0.56
    #
    # Total = 0.71

    assert predicted_rate == pytest.approx(
        0.71
    )


def test_recent_window_is_limited():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50,
        window_size=3
    )


    estimator.record_outcome(True)
    estimator.record_outcome(True)
    estimator.record_outcome(False)
    estimator.record_outcome(False)


    # Only the latest 3 outcomes remain:
    #
    # True
    # False
    # False
    #
    # Answer rate = 1 / 3

    recent_rate = (
        estimator.get_recent_answer_rate()
    )


    assert recent_rate == pytest.approx(
        1 / 3
    )


def test_prediction_reacts_to_answer_rate_drop():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.70,
        historical_weight=0.3,
        recent_weight=0.7
    )


    # Campaign behaviour suddenly drops.
    #
    # Only 1 out of 10 answers.

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


    predicted_rate = (
        estimator.predict_answer_rate()
    )


    # Historical = 0.70
    # Recent = 0.10
    #
    # Prediction:
    # 0.3 * 0.70 + 0.7 * 0.10
    # = 0.28

    assert predicted_rate == pytest.approx(
        0.28
    )


def test_statistics_are_explainable():

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )


    estimator.record_outcome(True)
    estimator.record_outcome(False)


    statistics = (
        estimator.get_statistics()
    )


    assert (
        statistics["historical_answer_rate"]
        == 0.50
    )

    assert (
        statistics["recent_answer_rate"]
        == 0.50
    )

    assert (
        statistics["recent_sample_size"]
        == 2
    )

    assert (
        statistics["predicted_answer_rate"]
        == pytest.approx(0.50)
    )


def test_invalid_historical_rate_raises_error():

    with pytest.raises(ValueError):

        AnswerRateEstimator(
            historical_answer_rate=1.5
        )