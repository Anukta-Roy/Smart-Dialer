from app.database.database import SessionLocal
from app.models.agent import Agent, AgentState
from app.services.reservation_service import reserve_agent


def test_only_one_reservation():

    db = SessionLocal()

    agent = Agent(
        name="Test Agent",
        state=AgentState.AVAILABLE
    )

    db.add(agent)
    db.commit()

    agent_id = agent.id

    first_attempt = reserve_agent(
        db,
        agent_id
    )

    second_attempt = reserve_agent(
        db,
        agent_id
    )

    assert first_attempt is True

    assert second_attempt is False

    db.delete(agent)
    db.commit()

    db.close()