from dataclasses import dataclass

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.pacing_engine import (
    PredictivePacingEngine,
    PacingInput,
    PacingDecision
)

from app.services.safety_controller import (
    SafetyController,
    SafetyInput,
    SafetyDecision
)


@dataclass
class DialingDecision:

    requested_calls: int

    allowed_calls: int

    predicted_answer_rate: float

    safe: bool

    pacing_reason: str

    safety_reason: str


class DialingCoordinator:
    """
    Coordinates predictive pacing and safety.

    Important:
    This class does NOT directly create calls.

    Its responsibility is:

    1. Estimate answer probability
    2. Ask the pacing engine how many calls
       should be attempted
    3. Pass that request to the Safety Controller
    4. Return the independently approved number

    The actual Progressive Dialer is responsible
    for selecting borrowers and agents and using
    the atomic call allocation transaction.
    """

    def __init__(
        self,
        answer_rate_estimator: AnswerRateEstimator,
        safety_controller: SafetyController
    ):

        self.answer_rate_estimator = (
            answer_rate_estimator
        )

        self.pacing_engine = (
            PredictivePacingEngine(
                answer_rate_estimator=
                answer_rate_estimator
            )
        )

        self.safety_controller = (
            safety_controller
        )


    def calculate(
        self,
        available_agents: int,
        connected_calls: int,
        ringing_calls: int,
        provider_health: float = 1.0
    ) -> DialingDecision:

        # ------------------------------------
        # STEP 1
        # Predictive pacing requests calls
        # ------------------------------------

        pacing_input = PacingInput(
            available_agents=available_agents,
            connected_calls=connected_calls,
            ringing_calls=ringing_calls,
            provider_health=provider_health
        )


        pacing_decision: PacingDecision = (
            self.pacing_engine.calculate(
                pacing_input
            )
        )


        # ------------------------------------
        # STEP 2
        # Safety independently evaluates
        # the predictive request
        # ------------------------------------

        safety_input = SafetyInput(
            requested_calls=
            pacing_decision.requested_calls,

            available_agents=
            available_agents,

            connected_calls=
            connected_calls,

            ringing_calls=
            ringing_calls,

            provider_health=
            provider_health
        )


        safety_decision: SafetyDecision = (
            self.safety_controller.evaluate(
                safety_input
            )
        )


        # ------------------------------------
        # STEP 3
        # Return the final decision
        # ------------------------------------

        return DialingDecision(

            requested_calls=
            pacing_decision.requested_calls,

            allowed_calls=
            safety_decision.allowed_calls,

            predicted_answer_rate=
            pacing_decision.predicted_answer_rate,

            safe=
            safety_decision.safe,

            pacing_reason=
            pacing_decision.reason,

            safety_reason=
            safety_decision.reason
        )