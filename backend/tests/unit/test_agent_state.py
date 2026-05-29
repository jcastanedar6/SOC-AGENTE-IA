from app.agent.state import AgentState


def test_initial_state():
    state = AgentState()
    assert state.is_running == False
    assert state.last_run is None
    assert state.events_processed == 0
    assert state.incidents_created == 0
    assert state.notifications_sent == 0
    assert state.errors == []


def test_reset_cycle():
    state = AgentState()
    state.events_processed = 10
    state.incidents_created = 2
    state.notifications_sent = 1
    state.errors = ["error1"]

    state.reset_cycle()

    assert state.last_run is not None
    assert state.events_processed == 10
    assert state.incidents_created == 2
    assert state.notifications_sent == 1
    assert state.errors == []


def test_record_error():
    state = AgentState()
    state.record_error("connection timeout")
    assert len(state.errors) == 1
    assert "connection timeout" in state.errors[0]


def test_error_max_size():
    state = AgentState()
    for i in range(60):
        state.record_error(f"error_{i}")
    assert len(state.errors) == 50
    assert not any("error_9" in e for e in state.errors)
    assert any("error_59" in e for e in state.errors)


def test_to_dict():
    state = AgentState()
    state.events_processed = 5
    state.record_error("test error")
    d = state.to_dict()
    assert d["is_running"] == False
    assert d["events_processed"] == 5
    assert len(d["errors"]) == 1
    assert d["last_run"] is None
