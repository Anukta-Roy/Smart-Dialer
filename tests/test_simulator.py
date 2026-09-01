from app.simulation.simulator import (
    run_scenario_a,
    run_scenario_b,
    run_scenario_c,
    run_scenario_d,
    run_all_scenarios
)


# =================================================
# SCENARIO A
# =================================================

def test_scenario_a_runs():

    result = run_scenario_a()

    assert result.scenario_name == "Scenario A"

    assert result.available_agents == 100

    assert result.predicted_answer_rate > 0

    assert result.requested_calls >= 0

    assert result.allowed_calls >= 0


# =================================================
# SCENARIO B
# =================================================

def test_scenario_b_runs():

    result = run_scenario_b()

    assert result.scenario_name == "Scenario B"

    assert result.available_agents == 100

    assert result.predicted_answer_rate > 0

    assert result.allowed_calls >= 0


# =================================================
# SCENARIO C
# =================================================

def test_scenario_c_runs():

    result = run_scenario_c()

    assert result.scenario_name == "Scenario C"

    assert result.available_agents == 100

    assert result.predicted_answer_rate > 0

    assert result.allowed_calls >= 0


# =================================================
# SCENARIO D
# =================================================

def test_scenario_d_runs_with_changing_conditions():

    results = run_scenario_d()

    assert len(results) == 3


    phase_1 = results[0]

    phase_2 = results[1]

    phase_3 = results[2]


    assert phase_1.scenario_name == (
        "Scenario D - Phase 1"
    )

    assert phase_2.scenario_name == (
        "Scenario D - Phase 2"
    )

    assert phase_3.scenario_name == (
        "Scenario D - Phase 3"
    )


    # Agent availability drops over time.

    assert (
        phase_1.available_agents
        > phase_2.available_agents
        > phase_3.available_agents
    )


    # Provider health degrades.

    assert (
        phase_1.provider_health
        > phase_2.provider_health
        > phase_3.provider_health
    )


# =================================================
# RUN ALL SCENARIOS
# =================================================

def test_run_all_scenarios():

    results = run_all_scenarios()


    assert "scenario_a" in results

    assert "scenario_b" in results

    assert "scenario_c" in results

    assert "scenario_d" in results


    assert (
        results["scenario_a"]
        .scenario_name
        == "Scenario A"
    )


    assert (
        len(
            results["scenario_d"]
        )
        == 3
    )