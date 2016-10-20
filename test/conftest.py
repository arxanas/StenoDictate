import pytest

from stenodictate.state import app_state

_UI_TIMEOUT = 10
"""Number of seconds to wait before killing a UI test."""


@pytest.fixture(autouse=True)
def state_path(tmpdir):
    path = tmpdir.mkdir("pytest_stenodictate")
    app_state._init(str(path))
    return path
