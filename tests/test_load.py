import time

import pytest

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.safety_controller import (
    SafetyController
)

from app.services.dialing_coordinator import (
    DialingCoordinator
)


@pytest.mark.parametrize(
    "available_agents",
    [
        100,
        1_000,
        10_000
    ]
)
def test_predictive_dialing_load(
    available_agents
):
    """
    Basic load test.

    Simulates repeated predictive dialing decisions
    at different campaign sizes.

    The test verifies that:

    1. The system produces valid decisions.
    2. Allowed calls never exceed available capacity.
    3. No negative dialing decision is produced.
    4. The predictive pipeline can handle repeated
       calculations at increasing scale.
    """

    estimator = AnswerRateEstimator(
        historical_answer_rate=0.50
    )

    safety_controller = SafetyController()

    coordinator = DialingCoordinator(
        answer_rate_estimator=estimator,
        safety_controller=safety_controller
    )


    # ---------------------------------------------
    # Add some realistic recent campaign behaviour
    # ---------------------------------------------

    for index in range(100):

        # Approximately 50% answer rate.
        estimator.record_outcome(
            answered=(index % 2 == 0)
        )


    iterations = 1_000

    total_requested_calls = 0

    total_allowed_calls = 0

    safety_violations = 0


    start_time = time.perf_counter()


    for index in range(iterations):

        # Simulate changing campaign conditions.

        connected_calls = (
            index
            %
            max(
                1,
                available_agents // 4
            )
        )


        ringing_calls = (
            index
            %
            max(
                1,
                available_agents // 10
            )
        )


        decision = coordinator.calculate(

            available_agents=available_agents,

            connected_calls=connected_calls,

            ringing_calls=ringing_calls,

            provider_health=1.0
        )


        total_requested_calls += (
            decision.requested_calls
        )


        total_allowed_calls += (
            decision.allowed_calls
        )


        # -----------------------------------------
        # Safety verification
        # -----------------------------------------

        if (
            decision.allowed_calls < 0
        ):
            safety_violations += 1


        if (
            decision.allowed_calls
            >
            available_agents
        ):
            safety_violations += 1


        if (
            connected_calls
            +
            decision.allowed_calls
            >
            available_agents
        ):
            safety_violations += 1


    elapsed_time = (
        time.perf_counter()
        -
        start_time
    )


    # ---------------------------------------------
    # Final assertions
    # ---------------------------------------------

    assert total_requested_calls >= 0

    assert total_allowed_calls >= 0

    assert safety_violations == 0


    print(
        "\n"
        f"\nLoad Test Results"
        f"\n-----------------"
        f"\nAvailable agents: {available_agents}"
        f"\nIterations: {iterations}"
        f"\nTotal requested calls: "
        f"{total_requested_calls}"
        f"\nTotal allowed calls: "
        f"{total_allowed_calls}"
        f"\nSafety violations: "
        f"{safety_violations}"
        f"\nExecution time: "
        f"{elapsed_time:.4f} seconds"
    )