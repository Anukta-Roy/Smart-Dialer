from dataclasses import dataclass


@dataclass
class SafetyInput:

    requested_calls: int

    available_agents: int

    connected_calls: int

    ringing_calls: int

    provider_health: float


@dataclass
class SafetyDecision:

    allowed_calls: int

    safe: bool

    reason: str


class SafetyController:
    """
    Independent safety boundary for predictive dialing.

    The Predictive Pacing Engine may request calls,
    but this controller determines the maximum number
    that may actually be initiated.

    This class does not initiate calls.
    """

    def __init__(
        self,
        max_calls_per_available_agent: int = 2,
        max_ringing_per_available_agent: int = 1
    ):

        if max_calls_per_available_agent <= 0:
            raise ValueError(
                "max_calls_per_available_agent "
                "must be greater than 0"
            )

        if max_ringing_per_available_agent < 0:
            raise ValueError(
                "max_ringing_per_available_agent "
                "cannot be negative"
            )

        self.max_calls_per_available_agent = (
            max_calls_per_available_agent
        )

        self.max_ringing_per_available_agent = (
            max_ringing_per_available_agent
        )

    def evaluate(
        self,
        safety_input: SafetyInput
    ) -> SafetyDecision:

        # ---------------------------------
        # Provider unavailable
        #
        # This must be checked before
        # requested_calls == 0.
        #
        # Even if the pacing engine requests
        # zero calls, a provider outage is an
        # unsafe / blocked operating condition.
        # ---------------------------------

        if safety_input.provider_health <= 0:

            return SafetyDecision(
                allowed_calls=0,
                safe=False,
                reason="Provider unavailable"
            )

        # ---------------------------------
        # No available agents
        # ---------------------------------

        if safety_input.available_agents <= 0:

            return SafetyDecision(
                allowed_calls=0,
                safe=False,
                reason="No agents available"
            )

        # ---------------------------------
        # Nothing requested
        #
        # This is a normal safe condition,
        # not a system failure.
        # ---------------------------------

        if safety_input.requested_calls <= 0:

            return SafetyDecision(
                allowed_calls=0,
                safe=True,
                reason="No additional calls requested"
            )

        # ---------------------------------
        # Calculate current free capacity
        # ---------------------------------

        free_agent_capacity = max(
            safety_input.available_agents
            -
            safety_input.connected_calls,
            0
        )

        if free_agent_capacity == 0:

            return SafetyDecision(
                allowed_calls=0,
                safe=False,
                reason=(
                    "No free agent capacity "
                    "after connected calls"
                )
            )

        # ---------------------------------
        # Maximum calls allowed based on
        # agent capacity
        # ---------------------------------

        maximum_calls = (
            free_agent_capacity
            *
            self.max_calls_per_available_agent
        )

        # ---------------------------------
        # Ringing safety limit
        # ---------------------------------

        maximum_ringing = (
            free_agent_capacity
            *
            self.max_ringing_per_available_agent
        )

        remaining_ringing_capacity = max(
            maximum_ringing
            -
            safety_input.ringing_calls,
            0
        )

        # ---------------------------------
        # Final independent safety cap
        #
        # The predictive engine cannot exceed
        # any of these limits.
        # ---------------------------------

        allowed_calls = min(
            safety_input.requested_calls,
            maximum_calls,
            remaining_ringing_capacity
        )

        # ---------------------------------
        # Safety reduced the prediction
        # ---------------------------------

        if allowed_calls < safety_input.requested_calls:

            return SafetyDecision(
                allowed_calls=allowed_calls,
                safe=False,
                reason=(
                    "Predictive request reduced "
                    "by independent safety limits"
                )
            )

        # ---------------------------------
        # Request is within all limits
        # ---------------------------------

        return SafetyDecision(
            allowed_calls=allowed_calls,
            safe=True,
            reason=(
                "Predictive request is within "
                "all safety limits"
            )
        )