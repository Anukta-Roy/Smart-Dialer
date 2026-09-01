from dataclasses import dataclass
from math import ceil

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)


@dataclass
class PacingInput:

    available_agents: int

    connected_calls: int

    ringing_calls: int

    provider_health: float = 1.0


@dataclass
class PacingDecision:

    requested_calls: int

    predicted_answer_rate: float

    free_agent_capacity: int

    reason: str


class PredictivePacingEngine:

    def __init__(
        self,
        answer_rate_estimator: AnswerRateEstimator
    ):

        self.answer_rate_estimator = (
            answer_rate_estimator
        )


    def calculate(
        self,
        pacing_input: PacingInput
    ) -> PacingDecision:
        """
        Calculate the number of additional calls
        the predictive pacing engine recommends.

        The engine only REQUESTS a number.

        It does not:
        - reserve agents
        - reserve borrowers
        - create calls
        - contact telecom providers

        The Safety Controller remains responsible
        for deciding what is actually allowed.
        """

        # ----------------------------------------
        # Basic agent availability validation
        # ----------------------------------------

        if pacing_input.available_agents <= 0:

            return PacingDecision(
                requested_calls=0,
                predicted_answer_rate=0.0,
                free_agent_capacity=0,
                reason="No agents available"
            )


        # ----------------------------------------
        # Provider health validation
        # ----------------------------------------

        if pacing_input.provider_health <= 0:

            return PacingDecision(
                requested_calls=0,
                predicted_answer_rate=0.0,
                free_agent_capacity=0,
                reason="Provider unavailable"
            )


        # ----------------------------------------
        # Adaptive answer probability
        # ----------------------------------------

        predicted_answer_rate = (
            self.answer_rate_estimator
            .predict_answer_rate()
        )


        if predicted_answer_rate <= 0:

            return PacingDecision(
                requested_calls=0,
                predicted_answer_rate=0.0,
                free_agent_capacity=0,
                reason="Predicted answer rate is zero"
            )


        # ----------------------------------------
        # Free agent capacity
        # ----------------------------------------

        free_agent_capacity = (
            pacing_input.available_agents
            -
            pacing_input.connected_calls
        )


        free_agent_capacity = max(
            free_agent_capacity,
            0
        )


        if free_agent_capacity == 0:

            return PacingDecision(
                requested_calls=0,
                predicted_answer_rate=(
                    predicted_answer_rate
                ),
                free_agent_capacity=0,
                reason=(
                    "No free capacity after "
                    "connected calls"
                )
            )


        # ----------------------------------------
        # Predict required dial attempts
        # ----------------------------------------
        #
        # Expected answers:
        #
        # calls_started * answer_rate
        #
        # To fill free capacity:
        #
        # calls_started =
        # free_capacity / answer_rate
        #

        expected_total_calls = ceil(
            free_agent_capacity
            /
            predicted_answer_rate
        )


        # ----------------------------------------
        # Ringing calls already consume
        # expected future agent capacity
        # ----------------------------------------

        requested_calls = (
            expected_total_calls
            -
            pacing_input.ringing_calls
        )


        # ----------------------------------------
        # Provider health adjustment
        # ----------------------------------------

        requested_calls = int(
            requested_calls
            *
            pacing_input.provider_health
        )


        requested_calls = max(
            requested_calls,
            0
        )


        return PacingDecision(
            requested_calls=requested_calls,
            predicted_answer_rate=(
                predicted_answer_rate
            ),
            free_agent_capacity=(
                free_agent_capacity
            ),
            reason=(
                "Adaptive pacing based on "
                "agent capacity, connected calls, "
                "ringing calls, predicted answer "
                "rate and provider health"
            )
        )