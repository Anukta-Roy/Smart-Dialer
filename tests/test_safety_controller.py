from app.services.safety_controller import (
    SafetyController,
    SafetyInput
)


def test_safe_request_is_allowed():

    controller = SafetyController(
        max_calls_per_available_agent=2,
        max_ringing_per_available_agent=1
    )


    safety_input = SafetyInput(
        requested_calls=5,
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = controller.evaluate(
        safety_input
    )


    assert decision.allowed_calls == 5
    assert decision.safe is True


def test_request_is_reduced_by_capacity_limit():

    controller = SafetyController(
        max_calls_per_available_agent=2,
        max_ringing_per_available_agent=10
    )


    safety_input = SafetyInput(
        requested_calls=30,
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = controller.evaluate(
        safety_input
    )


    # 10 free agents * 2
    # = maximum 20 calls

    assert decision.allowed_calls == 20
    assert decision.safe is False


def test_ringing_limit_blocks_new_calls():

    controller = SafetyController(
        max_calls_per_available_agent=10,
        max_ringing_per_available_agent=1
    )


    safety_input = SafetyInput(
        requested_calls=10,
        available_agents=5,
        connected_calls=0,
        ringing_calls=5,
        provider_health=1.0
    )


    decision = controller.evaluate(
        safety_input
    )


    # Maximum ringing:
    # 5 free agents * 1 = 5
    #
    # Already ringing = 5
    #
    # Remaining = 0

    assert decision.allowed_calls == 0
    assert decision.safe is False


def test_no_agents_blocks_calls():

    controller = SafetyController()


    safety_input = SafetyInput(
        requested_calls=5,
        available_agents=0,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = controller.evaluate(
        safety_input
    )


    assert decision.allowed_calls == 0
    assert decision.safe is False


def test_provider_outage_blocks_calls():

    controller = SafetyController()


    safety_input = SafetyInput(
        requested_calls=5,
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=0.0
    )


    decision = controller.evaluate(
        safety_input
    )


    assert decision.allowed_calls == 0
    assert decision.safe is False


def test_zero_request_is_safe():

    controller = SafetyController()


    safety_input = SafetyInput(
        requested_calls=0,
        available_agents=10,
        connected_calls=0,
        ringing_calls=0,
        provider_health=1.0
    )


    decision = controller.evaluate(
        safety_input
    )


    assert decision.allowed_calls == 0
    assert decision.safe is True