import sys
import threading

from PyQt5.QtWidgets import QApplication
import pytest

from stenodictate.state import app_state

_UI_TIMEOUT = 5
"""Number of seconds to wait before killing a UI test."""


@pytest.fixture(autouse=True)
def state_path(tmpdir):
    path = tmpdir.mkdir("pytest_stenodictate")
    app_state._init(str(path))
    return path


@pytest.yield_fixture
def app():
    app = QApplication(sys.argv)
    app_finished = threading.Event()

    class outer(object):
        timed_out = False

    def quit_app():
        if not app_finished.wait(_UI_TIMEOUT):
            app.exit(1)
            outer.timed_out = True

    timeout = threading.Thread(target=quit_app)
    timeout.start()
    try:
        yield app
        app_finished.set()
        timeout.join()
    finally:
        assert not outer.timed_out, (
            "UI test exceeded time limit of {} seconds.".format(_UI_TIMEOUT)
        )
        app.quit()
