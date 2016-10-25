import contextlib

import mock

from stenodictate.qdictate import Dictator


@contextlib.contextmanager
def stop_dictator(dictator):
    """Create a Dictator object, and ensure it stops."""
    try:
        yield
    finally:
        dictator.stop()


@mock.patch("pyttsx.init")
def test_started_dictation_signal(init, qtbot):
    engine = mock.Mock()
    callbacks = {}

    def connect(name, func):
        callbacks[name] = func
    engine.connect.side_effect = connect
    init.return_value = engine

    dictator = Dictator(parent=None)
    with stop_dictator(dictator):
        with qtbot.waitSignal(dictator.started_dictation):
            dictator.start(text="foo", rate=200)
            callbacks["started-word"](None, 0, 1)

        with qtbot.assertNotEmitted(dictator.started_dictation):
            callbacks["started-word"](None, 0, 1)
