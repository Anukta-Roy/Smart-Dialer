from collections import deque


class AnswerRateEstimator:
    """
    Adaptive answer-rate estimator.

    It combines:
    1. Historical answer rate
    2. Recent campaign outcomes

    Recent outcomes receive more importance so the
    pacing engine can react when campaign behaviour
    changes.
    """

    def __init__(
        self,
        historical_answer_rate: float,
        window_size: int = 100,
        historical_weight: float = 0.3,
        recent_weight: float = 0.7
    ):

        if not 0 <= historical_answer_rate <= 1:
            raise ValueError(
                "historical_answer_rate must be between 0 and 1"
            )

        if window_size <= 0:
            raise ValueError(
                "window_size must be greater than 0"
            )

        if historical_weight < 0:
            raise ValueError(
                "historical_weight cannot be negative"
            )

        if recent_weight < 0:
            raise ValueError(
                "recent_weight cannot be negative"
            )

        if (
            historical_weight + recent_weight
            <= 0
        ):
            raise ValueError(
                "At least one weight must be greater than 0"
            )


        self.historical_answer_rate = (
            historical_answer_rate
        )

        self.window_size = window_size

        self.historical_weight = (
            historical_weight
        )

        self.recent_weight = recent_weight


        # True = answered
        # False = not answered
        self.recent_outcomes = deque(
            maxlen=window_size
        )


    def record_outcome(
        self,
        answered: bool
    ):
        """
        Record one completed dialing outcome.

        answered=True  -> borrower answered
        answered=False -> borrower did not answer
        """

        self.recent_outcomes.append(
            answered
        )


    def get_recent_answer_rate(self):
        """
        Calculate the answer rate from the recent
        rolling window.
        """

        if len(self.recent_outcomes) == 0:

            return None


        answered_count = sum(
            self.recent_outcomes
        )


        return (
            answered_count
            /
            len(self.recent_outcomes)
        )


    def predict_answer_rate(self):
        """
        Return the adaptive predicted answer rate.

        If there is no recent campaign data,
        use the historical answer rate.

        Otherwise combine historical and recent
        campaign behaviour.
        """

        recent_answer_rate = (
            self.get_recent_answer_rate()
        )


        # No recent observations yet.
        if recent_answer_rate is None:

            return (
                self.historical_answer_rate
            )


        total_weight = (
            self.historical_weight
            +
            self.recent_weight
        )


        normalized_historical_weight = (
            self.historical_weight
            /
            total_weight
        )

        normalized_recent_weight = (
            self.recent_weight
            /
            total_weight
        )


        predicted_rate = (

            normalized_historical_weight
            *
            self.historical_answer_rate

            +

            normalized_recent_weight
            *
            recent_answer_rate

        )


        return predicted_rate


    def get_statistics(self):
        """
        Return explainable statistics for logging,
        simulation and debugging.
        """

        recent_answer_rate = (
            self.get_recent_answer_rate()
        )


        return {

            "historical_answer_rate":
                self.historical_answer_rate,

            "recent_answer_rate":
                recent_answer_rate,

            "predicted_answer_rate":
                self.predict_answer_rate(),

            "recent_sample_size":
                len(self.recent_outcomes)

        }