from app.simulation.simulator import (
    run_campaign_scenario_a,
    run_campaign_scenario_b,
    run_campaign_scenario_c
)


def test_campaign_scenario_a():

    result = run_campaign_scenario_a()

    assert result.total_steps == 20

    assert result.total_calls_initiated >= 0

    assert result.total_calls_answered >= 0

    assert result.total_calls_connected >= 0

    assert (
        result.total_calls_connected
        <=
        result.total_calls_answered
    )

    assert 0 <= (
        result.average_agent_utilization
    ) <= 1


def test_campaign_scenario_b():

    result = run_campaign_scenario_b()

    assert result.total_steps == 20

    assert len(result.steps) == 20

    assert (
        result.total_calls_initiated
        >=
        result.total_calls_answered
    )

    assert 0 <= (
        result.final_predicted_answer_rate
    ) <= 1


def test_campaign_scenario_c():

    result = run_campaign_scenario_c()

    assert result.total_steps == 20

    assert len(result.steps) == 20

    assert (
        result.total_calls_answered
        >= 0
    )

    assert (
        result.total_calls_connected
        >= 0
    )


def test_connected_calls_never_exceed_agent_capacity():

    result = run_campaign_scenario_c()

    for step in result.steps:

        assert (
            step.active_calls
            <= 100
        )


def test_simulation_is_reproducible():

    first = run_campaign_scenario_b()

    second = run_campaign_scenario_b()

    assert (
        first.total_calls_initiated
        ==
        second.total_calls_initiated
    )

    assert (
        first.total_calls_answered
        ==
        second.total_calls_answered
    )

    assert (
        first.total_calls_connected
        ==
        second.total_calls_connected
    )