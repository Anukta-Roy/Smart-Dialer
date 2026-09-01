# SmartDialer

A safety-first SmartDialer functional prototype that combines predictive dialing efficiency with the deterministic safety characteristics of progressive dialing.

The system uses an adaptive answer-rate estimator and predictive pacing engine to estimate how aggressively calls can be initiated. However, predictive logic never directly initiates calls. Every dialing request passes through a separate Safety Controller before resource allocation and provider initiation.

This creates a strict safety boundary:

```text
Campaign / Runtime State
        ↓
Predictive Pacing Engine
        ↓
Safety Controller
        ↓
Dialing Coordinator
        ↓
Controlled Progressive Dialer
        ↓
Atomic Call Allocation
        ↓
Telecom Provider
```

The project implements progressive dialing, predictive pacing, safety controls, atomic resource allocation, provider abstraction, idempotent recovery, event handling, crash recovery, simulation, and load testing.

---

# Features

## Progressive Dialing

The progressive dialing mechanism ensures that calls are allocated only when resources are available.

The system:

- finds available agents;
- finds available borrowers;
- reserves both resources;
- creates a call in the `RESERVED` state;
- prevents allocation beyond available agent capacity.

---

## Predictive Dialing

The predictive pacing engine determines how many additional calls may be requested based on:

- available agents;
- connected calls;
- ringing calls;
- provider health;
- historical answer rate;
- recent campaign outcomes.

The predictive algorithm only produces a requested number of calls.

It does not directly initiate calls.

---

## Safety Controller

The Safety Controller is a mandatory safety boundary between predictive pacing and call allocation.

It can:

- approve a dialing request;
- reduce the requested number of calls;
- block dialing;
- prevent dialing when no agents are available;
- prevent dialing during provider outages;
- limit calls based on current capacity;
- block unsafe ringing-call conditions.

The predictive pacing engine cannot bypass this safety mechanism.

---

## Adaptive Answer Rate Estimation

The `AnswerRateEstimator` combines:

1. historical answer rate;
2. recent campaign outcomes.

Recent outcomes are maintained using a rolling window.

The predicted answer rate is calculated using weighted historical and recent behavior.

This allows the pacing system to react when campaign conditions change.

For example:

```text
Historical Answer Rate: 50%
Recent Answer Rate:     10%

↓ Adaptive Prediction

Predicted Answer Rate decreases

↓ Predictive Pacing

Fewer calls requested

↓ Safety Controller

Unsafe requests are further reduced or blocked
```

---

# Architecture

The complete architecture diagram is available in:

```text
ARCHITECTURE.md
```

The main system flow is:

```text
Campaign & Runtime Inputs
        │
        ▼
Answer Rate Estimator
        │
        ▼
Predictive Pacing Engine
        │
        ▼
Safety Controller
        │
        ▼
Dialing Coordinator
        │
        ▼
Controlled Progressive Dialer
        │
        ▼
Progressive Dialer
        │
        ▼
Atomic Call Allocation
        │
        ▼
Provider Initiation & Recovery
        │
        ▼
Telecom Provider
        │
        ▼
Provider Events
        │
        ▼
Call State Service
        │
        ▼
PostgreSQL
```

Completed call outcomes are fed back into the answer-rate estimator, allowing predictive pacing to adapt to recent campaign behavior.

---

# Project Structure

```text
smart-dialer/
│
├── app/
│   │
│   ├── database/
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── agent.py
│   │   ├── borrower.py
│   │   └── call.py
│   │
│   ├── providers/
│   │   ├── base_provider.py
│   │   ├── provider_a.py
│   │   └── provider_b.py
│   │
│   ├── services/
│   │   ├── call_allocator.py
│   │   ├── progressive_dialer.py
│   │   ├── controlled_progressive_dialer.py
│   │   ├── answer_rate_estimator.py
│   │   ├── pacing_engine.py
│   │   ├── safety_controller.py
│   │   ├── dialing_coordinator.py
│   │   ├── recovery_service.py
│   │   └── worker_crash_recovery.py
│   │
│   └── simulation/
│       ├── simulator.py
│       └── campaign_simulator.py
│
├── tests/
│   ├── test_agent_reservation.py
│   ├── test_borrower_reservation.py
│   ├── test_call_events.py
│   ├── test_call_state.py
│   ├── test_progressive.py
│   ├── test_provider_a.py
│   ├── test_provider_b.py
│   ├── test_recovery.py
│   ├── test_worker_crash_recovery.py
│   ├── test_answer_rate_estimator.py
│   ├── test_pacing_engine.py
│   ├── test_safety_controller.py
│   ├── test_dialing_coordinator.py
│   ├── test_controlled_progressive_dialer.py
│   ├── test_predictive_dialing_integration.py
│   ├── test_agent_availability_drop.py
│   ├── test_simulator.py
│   ├── test_campaign_simulator.py
│   └── test_load.py
│
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── README.md
├── requirements.txt
└── pytest.ini
```

---

# Requirements

- Python 3.11 or later
- PostgreSQL
- pip

---

# Installation

## 1. Clone or Extract the Project

If using Git:

```bash
git clone <repository-url>
cd smart-dialer
```

If submitting as a ZIP file, extract the project and open the project directory.

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate the environment:

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Database Configuration

The application uses PostgreSQL.

Database configuration is loaded from environment variables using `python-dotenv`.

The project includes an `.env.example` file.

Copy it to `.env`.

### Windows

```bash
copy .env.example .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Then update the database connection details.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/smartdialer
```

Replace:

```text
username
password
smartdialer
```

with your local PostgreSQL credentials and database name.

The `.env` file should not be committed because it may contain database credentials.

---

# Database Models

The system maintains persistent state for:

- agents;
- borrowers;
- calls.

PostgreSQL acts as the source of truth for allocation and call state.

---

# Agent State Machine

Agents follow an explicit lifecycle.

```text
OFFLINE
   │
   ▼
AVAILABLE
   │
   ▼
RESERVED
   │
   ▼
DIALING
   │
   ▼
CONNECTED
   │
   ▼
WRAP_UP
   │
   ▼
AVAILABLE
```

Additional states include:

```text
PAUSED
OFFLINE
```

The important allocation safety property is:

```text
AVAILABLE → RESERVED
```

An agent must not be reserved by multiple workers simultaneously.

---

# Borrower State

Borrowers can be allocated independently.

Typical states are:

```text
AVAILABLE
    │
    ▼
RESERVED
```

Atomic allocation prevents multiple workers from reserving the same borrower.

---

# Call State Machine

Calls use explicit state transitions.

```text
QUEUED
   │
   ▼
RESERVED
   │
   ▼
INITIATED
   │
   ▼
RINGING
   │
   ▼
ANSWERED
   │
   ▼
CONNECTED
   │
   ▼
COMPLETED
```

Failure states include:

```text
FAILED
CANCELLED
```

The call state service protects the system against:

- invalid state transitions;
- duplicate provider events;
- stale events;
- out-of-order events.

For example:

```text
ANSWERED
ANSWERED
ANSWERED
COMPLETED
```

does not cause multiple state transitions.

Similarly, stale events arriving after a later state do not move the call backward.

---

# Progressive Dialing

The progressive dialer follows a conservative allocation model:

```text
Available Agent
        +
Available Borrower
        ↓
Atomic Reservation
        ↓
Create RESERVED Call
```

The system stops allocating calls when either:

- no available agents remain;
- no available borrowers remain.

This ensures that the number of agent-bound outbound calls does not exceed available capacity.

---

# Predictive Pacing

Predictive pacing estimates how many additional calls may be started.

Inputs include:

```text
Available Agents
Connected Calls
Ringing Calls
Provider Health
Predicted Answer Rate
```

The pacing engine returns:

```text
Requested Calls
```

This value is only a prediction.

It is not a direct instruction to initiate calls.

---

# Safety Boundary

The predictive algorithm is separated from actual dialing.

```text
Predictive Pacing Engine
        │
        │ Requested Calls
        ▼
Safety Controller
        │
        │ Allowed / Reduced / Blocked
        ▼
Dialing Coordinator
        │
        ▼
Controlled Progressive Dialer
```

This architecture ensures that predictive logic cannot directly bypass deterministic safety checks.

The Safety Controller can reduce or reject a predictive request based on:

- available agent capacity;
- connected calls;
- ringing calls;
- provider health;
- zero available agents.

---

# Atomic Call Allocation

Call allocation reserves resources before initiating a provider call.

The allocation flow is:

```text
Find Available Agent
        │
        ▼
Reserve Agent
        │
        ▼
Find Available Borrower
        │
        ▼
Reserve Borrower
        │
        ▼
Create Call
State = RESERVED
```

If allocation fails, the transaction is rolled back.

This prevents inconsistent resource state when multiple workers attempt allocation concurrently.

---

# Telecom Provider Abstraction

The dialer uses a provider abstraction layer.

```text
BaseProvider
     │
     ├── Provider A
     │
     └── Provider B
```

The dialing logic does not need to know provider-specific implementation details.

---

## Provider A

Provider A simulates a provider with:

- fast response;
- reliable call initiation;
- ordered events.

---

## Provider B

Provider B simulates more difficult provider behavior:

- slower responses;
- occasional timeouts;
- duplicate events;
- out-of-order events.

This allows the system to test resilience against unreliable external systems.

---

# Provider Recovery and Idempotency

Provider initiation uses a recovery strategy.

```text
Call Record
    │
    ▼
Idempotency Check
    │
    ├── Already Initiated
    │       └── Reuse Existing Call
    │
    ▼
Primary Provider
    │
    ├── Success
    │
    └── Failure / Timeout
              │
              ▼
        Fallback Provider
```

The same database `Call` record is reused.

This prevents retries from creating duplicate calls.

If all providers fail:

```text
Call → FAILED

Agent → AVAILABLE

Borrower → AVAILABLE
```

Resources are released so that they are not permanently reserved.

---

# Provider Events

Provider events are processed asynchronously.

```text
Provider
   │
   ▼
Provider Event
   │
   ▼
Event Processor
   │
   ▼
Call State Service
   │
   ├── Validate Transition
   ├── Ignore Duplicate Event
   └── Ignore Out-of-Order Event
   │
   ▼
PostgreSQL
```

The system does not assume external providers always send events correctly.

---

# Worker Crash Recovery

The system includes recovery for reserved calls.

Example failure:

```text
Agent Reserved
      ↓
Borrower Reserved
      ↓
Call Created
      ↓
Worker Crashes
```

Recovery scans reserved calls and releases resources when necessary.

```text
Find Reserved Calls
        │
        ▼
Recover Call State
        │
        ▼
Release Reserved Agent
        │
        ▼
Release Reserved Borrower
```

This prevents resources from remaining permanently reserved after worker failure.

---

# Adaptive Feedback Loop

Completed call outcomes are fed back into the answer-rate estimator.

```text
Completed Calls
      │
      ▼
Recent Call Outcomes
      │
      ▼
Answer Rate Estimator
      │
      ▼
Updated Predicted Answer Rate
      │
      ▼
Predictive Pacing
```

This allows the dialer to react when recent campaign behavior changes.

For example, if answer rates suddenly decrease, the predicted answer rate changes and pacing decisions adapt.

---

# Simulation

The project includes a basic simulation layer.

The simulator evaluates different dialing conditions.

Examples include:

```text
Scenario A
Scenario B
Scenario C
Scenario D
```

Scenario D demonstrates changing runtime conditions, including:

- changing answer rates;
- decreasing agent availability;
- increasing ringing calls;
- degraded provider health;
- increased connected calls.

The simulation demonstrates how predictive pacing and safety decisions change as campaign conditions evolve.

---

# Campaign Simulation

The campaign simulator evaluates dialing behavior across campaign conditions.

The simulation verifies important safety properties, including:

```text
Connected Calls ≤ Agent Capacity
```

Simulation results are reproducible.

---

# Load Testing

The project includes a basic load test for predictive dialing.

The test evaluates scenarios with increasing numbers of available agents:

```text
100 agents
1,000 agents
10,000 agents
```

The load test checks that the predictive and safety pipeline continues to enforce safety constraints.

The prototype focuses on the correctness and efficiency of decision logic rather than placing thousands of real telecom calls.

---

# Running Tests

Run the complete test suite:

```bash
pytest -v
```

The project includes tests for:

- agent reservation;
- borrower reservation;
- call state transitions;
- duplicate events;
- out-of-order events;
- progressive dialing;
- provider behavior;
- fallback recovery;
- idempotency;
- worker crash recovery;
- adaptive answer-rate estimation;
- predictive pacing;
- safety controls;
- dialing coordination;
- controlled progressive dialing;
- agent availability drops;
- simulation;
- campaign simulation;
- load testing.

---

# Example Test Categories

Run a specific test file:

```bash
pytest tests/test_pacing_engine.py -v
```

Run safety tests:

```bash
pytest tests/test_safety_controller.py -v
```

Run provider recovery tests:

```bash
pytest tests/test_recovery.py -v
```

Run simulation tests:

```bash
pytest tests/test_simulator.py -v
```

Run load tests:

```bash
pytest tests/test_load.py -v
```

---

# Architecture Decisions

## Why PostgreSQL?

PostgreSQL is used as the persistent source of truth for:

- agent state;
- borrower state;
- call state;
- allocation state.

For this prototype, a relational database provides a simple way to model resource state and transactional allocation without introducing additional infrastructure.

---

## Why Not Let Predictive Logic Directly Dial?

Predictive models can be wrong.

A sudden change in answer rate, provider behavior, or agent availability could make a previously reasonable prediction unsafe.

Therefore:

```text
Prediction ≠ Permission
```

The pacing engine requests calls.

The Safety Controller determines whether those calls are actually allowed.

---

## Why Use a Separate Safety Controller?

Separating prediction from deterministic safety creates a clear architectural boundary.

The predictive component can optimize utilization, while the safety layer enforces hard constraints.

This allows the system to benefit from predictive behavior without allowing prediction errors to directly create unsafe dialing.

---

## Why Use Provider Abstraction?

The provider abstraction separates telecom behavior from dialing logic.

The dialer does not depend on provider-specific details.

Different providers can:

- fail differently;
- produce different event behavior;
- have different latency characteristics.

The core system remains independent of those implementation details.

---

## Why Reuse the Same Call Record During Retry?

Retries can cause duplicate provider calls if each retry creates a new call record.

The recovery service performs an idempotency check before initiating a provider call.

If the call already contains a provider call ID, it is reused instead of initiating another provider call.

---

# Scaling Considerations

The current implementation is a functional prototype.

At larger scales, the likely bottlenecks would include:

- database contention during concurrent agent reservation;
- high-frequency call-state updates;
- provider event processing;
- polling or querying for available resources;
- concurrent campaign coordination.

For larger deployments, possible improvements include:

- stronger database-level locking strategies;
- optimized indexes;
- partitioning campaign workloads;
- asynchronous job processing;
- event queues;
- distributed workers;
- caching read-heavy runtime metrics.

These should be introduced only when the scale requires them.

The prototype intentionally keeps the architecture relatively simple to prioritize correctness and explainability.

---

# Final Design Answer (Final Question)

The central design principle of SmartDialer is:

```text
Predict aggressively,
but enforce safety deterministically.
```

Predictive pacing improves potential agent utilization by estimating how many calls may be needed.
However, the Safety Controller remains the final authority before calls are allocated.
The resulting architecture aims to retain as much utilization benefit as possible from predictive dialing while preserving the deterministic safety properties of progressive dialing.

```text
Predictive Logic
      │
      │ Optimization
      ▼
Safety Controller
      │
      │ Deterministic Constraints
      ▼
Controlled Dialing
```

---

# Assignment Deliverables

This prototype includes:

- working source code;
- README with setup instructions;
- architecture diagram;
- agent state machine;
- call state machine;
- progressive dialer;
- predictive pacing engine;
- safety controller;
- mock telecom providers;
- tests;
- basic simulation;
- basic load testing;
- architecture decisions.

The implementation focuses on correctness, concurrency awareness, failure handling, safety, and explainable predictive behavior.