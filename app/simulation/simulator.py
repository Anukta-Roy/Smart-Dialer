from dataclasses import dataclass, field
import random

from app.services.answer_rate_estimator import (
    AnswerRateEstimator
)

from app.services.safety_controller import (
    SafetyController
)

from app.services.dialing_coordinator import (
    DialingCoordinator
)


# =================================================
# BASIC SIMULATION RESULT
# =================================================

@dataclass
class SimulationMetrics:

    scenario_name: str

    available_agents: int

    requested_calls: int

    allowed_calls: int

    predicted_answer_rate: float

    provider_health: float

    safe: bool

    pacing_reason: str

    safety_reason: str


# =================================================
# TIME-STEP SIMULATION METRICS
# =================================================

@dataclass
class CampaignStepMetrics:
    """
    Metrics produced during one simulation step.
    """

    step: int

    available_agents: int

    requested_calls: int

    allowed_calls: int

    calls_initiated: int

    calls_answered: int

    calls_connected: int

    calls_completed: int

    active_calls: int

    agent_utilization: float

    predicted_answer_rate: float

    provider_health: float

    safe: bool


@dataclass
class CampaignSimulationResult:
    """
    Complete result of a multi-step campaign simulation.
    """

    scenario_name: str

    total_steps: int

    total_calls_initiated: int

    total_calls_answered: int

    total_calls_connected: int

    total_calls_completed: int

    final_active_calls: int

    final_available_agents: int

    average_agent_utilization: float

    final_predicted_answer_rate: float

    safety_interventions: int

    steps: list[CampaignStepMetrics] = field(
        default_factory=list
    )


# =================================================
# DIALER SIMULATOR
# =================================================

class DialerSimulator:

    """
    SmartDialer simulation layer.

    Uses the application's real decision components:

        AnswerRateEstimator
                ↓
        DialingCoordinator
                ↓
        Predictive Pacing
                ↓
        SafetyController

    The simulation does not create PostgreSQL records.
    It is designed to exercise pacing and safety logic
    at campaign scale.
    """

    def __init__(
        self,
        historical_answer_rate: float,
        max_calls_per_available_agent: int = 2
    ):

        # ---------------------------------------------
        # Answer-rate estimator
        # ---------------------------------------------

        self.estimator = AnswerRateEstimator(
            historical_answer_rate=historical_answer_rate
        )


        # ---------------------------------------------
        # Safety controller
        # ---------------------------------------------

        self.safety_controller = SafetyController(

            max_calls_per_available_agent=(
                max_calls_per_available_agent
            ),

            max_ringing_per_available_agent=100
        )


        # ---------------------------------------------
        # Dialing coordinator
        # ---------------------------------------------

        self.coordinator = DialingCoordinator(

            answer_rate_estimator=self.estimator,

            safety_controller=self.safety_controller
        )


    # =================================================
    # RUN ONE BASIC SIMULATION STEP
    # =================================================

    def run_step(
        self,
        scenario_name: str,
        available_agents: int,
        connected_calls: int = 0,
        ringing_calls: int = 0,
        provider_health: float = 1.0
    ) -> SimulationMetrics:

        decision = self.coordinator.calculate(

            available_agents=available_agents,

            connected_calls=connected_calls,

            ringing_calls=ringing_calls,

            provider_health=provider_health
        )


        return SimulationMetrics(

            scenario_name=scenario_name,

            available_agents=available_agents,

            requested_calls=decision.requested_calls,

            allowed_calls=decision.allowed_calls,

            predicted_answer_rate=(
                decision.predicted_answer_rate
            ),

            provider_health=provider_health,

            safe=decision.safe,

            pacing_reason=decision.pacing_reason,

            safety_reason=decision.safety_reason
        )


    # =================================================
    # RUN TIME-STEP CAMPAIGN SIMULATION
    # =================================================

    def run_campaign(
        self,
        scenario_name: str,
        available_agents: int,
        answer_rate: float,
        average_talk_time: int,
        total_steps: int = 20,
        provider_health: float = 1.0,
        random_seed: int = 42
    ) -> CampaignSimulationResult:

        """
        Run a simplified time-step predictive dialing
        campaign simulation.

        Each simulation step:

        1. Existing calls may complete.
        2. Available agent capacity is recalculated.
        3. Predictive pacing calculates demand.
        4. Safety controller limits demand.
        5. Allowed calls are attempted.
        6. Provider health can cause initiation failure.
        7. Borrowers may answer.
        8. Answered calls consume agent capacity.
        9. Outcomes update the adaptive estimator.

        One simulation step represents 30 seconds.
        """

        # ---------------------------------------------
        # Validate inputs
        # ---------------------------------------------

        if available_agents < 0:
            raise ValueError(
                "available_agents cannot be negative"
            )


        if not 0 <= answer_rate <= 1:
            raise ValueError(
                "answer_rate must be between 0 and 1"
            )


        if average_talk_time <= 0:
            raise ValueError(
                "average_talk_time must be greater than 0"
            )


        if total_steps <= 0:
            raise ValueError(
                "total_steps must be greater than 0"
            )


        if not 0 <= provider_health <= 1:
            raise ValueError(
                "provider_health must be between 0 and 1"
            )


        # ---------------------------------------------
        # Deterministic random generator
        #
        # This makes simulation tests reproducible.
        # ---------------------------------------------

        random_generator = random.Random(
            random_seed
        )


        # ---------------------------------------------
        # Simulation state
        #
        # Each active call stores the number of
        # remaining simulation steps.
        # ---------------------------------------------

        active_calls = []

        total_calls_initiated = 0

        total_calls_answered = 0

        total_calls_connected = 0

        total_calls_completed = 0

        safety_interventions = 0

        utilization_values = []

        step_results = []


        # ---------------------------------------------
        # Time conversion
        #
        # One step = 30 seconds.
        # ---------------------------------------------

        step_duration_seconds = 30


        talk_time_steps = max(

            1,

            round(
                average_talk_time
                /
                step_duration_seconds
            )
        )


        # =================================================
        # MAIN SIMULATION LOOP
        # =================================================

        for step in range(
            1,
            total_steps + 1
        ):


            # ---------------------------------------------
            # COMPLETE FINISHED CALLS
            # ---------------------------------------------

            still_active_calls = []

            completed_this_step = 0


            for remaining_steps in active_calls:

                remaining_steps -= 1


                if remaining_steps <= 0:

                    completed_this_step += 1

                    total_calls_completed += 1

                else:

                    still_active_calls.append(
                        remaining_steps
                    )


            active_calls = (
                still_active_calls
            )


            # ---------------------------------------------
            # CURRENT AGENT CAPACITY
            # ---------------------------------------------

            connected_calls = len(
                active_calls
            )


            current_available_agents = max(

                0,

                available_agents
                -
                connected_calls
            )


            # ---------------------------------------------
            # RINGING CALLS
            #
            # The current compact simulation does not
            # maintain a separate multi-step ringing
            # queue, so this remains zero.
            # ---------------------------------------------

            ringing_calls = 0


            # ---------------------------------------------
            # CALCULATE PACING + SAFETY DECISION
            # ---------------------------------------------

            decision = (
                self.coordinator.calculate(

                    available_agents=(
                        current_available_agents
                    ),

                    connected_calls=(
                        connected_calls
                    ),

                    ringing_calls=(
                        ringing_calls
                    ),

                    provider_health=(
                        provider_health
                    )
                )
            )


            requested_calls = (
                decision.requested_calls
            )


            allowed_calls = (
                decision.allowed_calls
            )


            # ---------------------------------------------
            # SAFETY INTERVENTION
            #
            # Count whenever safety reduces the
            # predictive request.
            # ---------------------------------------------

            if (
                allowed_calls
                <
                requested_calls
            ):

                safety_interventions += 1


            # ---------------------------------------------
            # CALL INITIATION METRICS
            # ---------------------------------------------

            calls_initiated_this_step = 0

            calls_answered_this_step = 0

            calls_connected_this_step = 0


            # ---------------------------------------------
            # ATTEMPT ALLOWED CALLS
            # ---------------------------------------------

            for _ in range(
                allowed_calls
            ):


                # -----------------------------------------
                # PROVIDER HEALTH
                #
                # A provider_health of:
                #
                # 1.0 = no simulated provider failures
                # 0.0 = all attempts fail
                # -----------------------------------------

                provider_succeeds = (

                    random_generator.random()
                    <=
                    provider_health
                )


                if not provider_succeeds:

                    continue


                # -----------------------------------------
                # CALL INITIATED
                # -----------------------------------------

                calls_initiated_this_step += 1

                total_calls_initiated += 1


                # -----------------------------------------
                # BORROWER ANSWER OUTCOME
                # -----------------------------------------

                answered = (

                    random_generator.random()
                    <
                    answer_rate
                )


                # Feed actual simulated outcome into
                # the adaptive estimator.

                self.estimator.record_outcome(
                    answered=answered
                )


                # -----------------------------------------
                # ANSWERED
                # -----------------------------------------

                if answered:

                    calls_answered_this_step += 1

                    total_calls_answered += 1


                    # -------------------------------------
                    # CONNECT IF AGENT CAPACITY EXISTS
                    # -------------------------------------

                    if (

                        len(active_calls)
                        <
                        available_agents

                    ):

                        active_calls.append(
                            talk_time_steps
                        )


                        calls_connected_this_step += 1

                        total_calls_connected += 1


            # ---------------------------------------------
            # AGENT UTILIZATION
            # ---------------------------------------------

            active_agent_count = min(

                len(active_calls),

                available_agents
            )


            if available_agents > 0:

                agent_utilization = (

                    active_agent_count
                    /
                    available_agents
                )

            else:

                agent_utilization = 0.0


            utilization_values.append(
                agent_utilization
            )


            # ---------------------------------------------
            # STORE STEP RESULT
            # ---------------------------------------------

            step_results.append(

                CampaignStepMetrics(

                    step=step,

                    available_agents=(
                        current_available_agents
                    ),

                    requested_calls=(
                        requested_calls
                    ),

                    allowed_calls=(
                        allowed_calls
                    ),

                    calls_initiated=(
                        calls_initiated_this_step
                    ),

                    calls_answered=(
                        calls_answered_this_step
                    ),

                    calls_connected=(
                        calls_connected_this_step
                    ),

                    calls_completed=(
                        completed_this_step
                    ),

                    active_calls=(
                        len(active_calls)
                    ),

                    agent_utilization=(
                        agent_utilization
                    ),

                    predicted_answer_rate=(

                        self.estimator
                        .predict_answer_rate()

                    ),

                    provider_health=(
                        provider_health
                    ),

                    safe=(
                        decision.safe
                    )
                )
            )


        # =================================================
        # FINAL AGGREGATED METRICS
        # =================================================

        if len(utilization_values) > 0:

            average_agent_utilization = (

                sum(utilization_values)
                /
                len(utilization_values)
            )

        else:

            average_agent_utilization = 0.0


        final_available_agents = max(

            0,

            available_agents
            -
            len(active_calls)
        )


        return CampaignSimulationResult(

            scenario_name=scenario_name,

            total_steps=total_steps,

            total_calls_initiated=(
                total_calls_initiated
            ),

            total_calls_answered=(
                total_calls_answered
            ),

            total_calls_connected=(
                total_calls_connected
            ),

            total_calls_completed=(
                total_calls_completed
            ),

            final_active_calls=(
                len(active_calls)
            ),

            final_available_agents=(
                final_available_agents
            ),

            average_agent_utilization=(
                average_agent_utilization
            ),

            final_predicted_answer_rate=(

                self.estimator
                .predict_answer_rate()

            ),

            safety_interventions=(
                safety_interventions
            ),

            steps=(
                step_results
            )
        )


# =================================================
# BASIC SCENARIO A
# =================================================

def run_scenario_a():

    """
    Scenario A

    Historical answer rate:
        20%
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.20
    )


    return simulator.run_step(

        scenario_name="Scenario A",

        available_agents=100,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


# =================================================
# BASIC SCENARIO B
# =================================================

def run_scenario_b():

    """
    Scenario B

    Historical answer rate:
        50%
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.50
    )


    return simulator.run_step(

        scenario_name="Scenario B",

        available_agents=100,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


# =================================================
# BASIC SCENARIO C
# =================================================

def run_scenario_c():

    """
    Scenario C

    Historical answer rate:
        70%
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.70
    )


    return simulator.run_step(

        scenario_name="Scenario C",

        available_agents=100,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


# =================================================
# BASIC SCENARIO D
# =================================================

def run_scenario_d():

    """
    Scenario D

    Demonstrates changing campaign conditions.
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.50
    )


    results = []


    # ---------------------------------------------
    # PHASE 1
    #
    # Normal campaign conditions.
    # ---------------------------------------------

    phase_1 = simulator.run_step(

        scenario_name="Scenario D - Phase 1",

        available_agents=100,

        connected_calls=0,

        ringing_calls=0,

        provider_health=1.0
    )


    results.append(
        phase_1
    )


    # ---------------------------------------------
    # PHASE 2
    #
    # Recent answer rate drops.
    # ---------------------------------------------

    simulator.estimator.record_outcome(
        answered=False
    )

    simulator.estimator.record_outcome(
        answered=False
    )

    simulator.estimator.record_outcome(
        answered=False
    )

    simulator.estimator.record_outcome(
        answered=True
    )


    phase_2 = simulator.run_step(

        scenario_name="Scenario D - Phase 2",

        available_agents=80,

        connected_calls=10,

        ringing_calls=15,

        provider_health=0.8
    )


    results.append(
        phase_2
    )


    # ---------------------------------------------
    # PHASE 3
    #
    # Provider health degrades further.
    # ---------------------------------------------

    phase_3 = simulator.run_step(

        scenario_name="Scenario D - Phase 3",

        available_agents=60,

        connected_calls=20,

        ringing_calls=30,

        provider_health=0.4
    )


    results.append(
        phase_3
    )


    return results


# =================================================
# RUN ALL BASIC SCENARIOS
# =================================================

def run_all_scenarios():

    return {

        "scenario_a": run_scenario_a(),

        "scenario_b": run_scenario_b(),

        "scenario_c": run_scenario_c(),

        "scenario_d": run_scenario_d()
    }


# =================================================
# TIME-BASED CAMPAIGN SCENARIO A
# =================================================

def run_campaign_scenario_a():

    """
    Campaign Scenario A

    Answer rate:
        20%

    Average talk time:
        120 seconds
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.20
    )


    return simulator.run_campaign(

        scenario_name="Campaign Scenario A",

        available_agents=100,

        answer_rate=0.20,

        average_talk_time=120,

        total_steps=20,

        provider_health=1.0
    )


# =================================================
# TIME-BASED CAMPAIGN SCENARIO B
# =================================================

def run_campaign_scenario_b():

    """
    Campaign Scenario B

    Answer rate:
        50%

    Average talk time:
        90 seconds
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.50
    )


    return simulator.run_campaign(

        scenario_name="Campaign Scenario B",

        available_agents=100,

        answer_rate=0.50,

        average_talk_time=90,

        total_steps=20,

        provider_health=1.0
    )


# =================================================
# TIME-BASED CAMPAIGN SCENARIO C
# =================================================

def run_campaign_scenario_c():

    """
    Campaign Scenario C

    Answer rate:
        70%

    Average talk time:
        180 seconds
    """

    simulator = DialerSimulator(
        historical_answer_rate=0.70
    )


    return simulator.run_campaign(

        scenario_name="Campaign Scenario C",

        available_agents=100,

        answer_rate=0.70,

        average_talk_time=180,

        total_steps=20,

        provider_health=1.0
    )


# =================================================
# RUN ALL CAMPAIGN SCENARIOS
# =================================================

def run_all_campaign_scenarios():

    return {

        "scenario_a": run_campaign_scenario_a(),

        "scenario_b": run_campaign_scenario_b(),

        "scenario_c": run_campaign_scenario_c()
    }