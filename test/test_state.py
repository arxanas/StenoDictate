from stenodictate.state import app_state


def test_get_state_returns_none():
    assert app_state["foo"] is None


def test_can_get_old_state():
    app_state["foo"] = "foo"
    assert app_state["foo"] == "foo"
