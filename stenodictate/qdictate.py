"""Dictation wrapper around Pyttsx that works with PyQt.

If we try to launch the pyttsx event loop using a regular method like
`runAndWait`, it causes the program to crash with a segfault for some reason.
To get around this, we make our own event loop.

There is a relevant discussion about running pyttsx alongside a GUI event loop
here: https://github.com/RapidWareTech/pyttsx/issues/11.

It's also convenient to use the PyQt signals/slots mechanism.
"""
import threading

from PyQt5.QtCore import pyqtSignal, QObject, QThread
import pyttsx

_SLOW_DICTATION_RATE = 260
"""The speed at which to dictate individual words in slow dictation."""

_FAST_DICTATION_CUTOFF = 140
"""The speed, in wpm, at which to stop pronouncing words individually."""

_NUM_WORDS_PER_SYLLABLE = 1.0 / 1.44
"""This number was derived from a brochure about the EV360 software."""

_PUNCTUATION_PAUSES = {
    ".": 1.0,
    "?": 1.0,
    "!": 1.0,
    ";": 1.0,
    ":": 1.0,
    ",": 0.75,
}
"""The fraction of a word-length to pause after punctuation."""

_EVENT_LOOP_INTERVAL = 0.1
"""The amount of time to wait, in seconds, between event loop iterations."""


class _DictatorSignals(QObject):
    """The set of signals emitted by the dictator."""

    started_word = pyqtSignal(int)
    """Emitted when a new word has started to be spoken.

    The index of the word in the text is passed as a parameter.

    TODO: This might not actually work if the text is paused and then
    restarted. It might require that we give all the words their own names, or
    something like that.
    """

    done = pyqtSignal()
    """Emitted when the dictation has finished."""


class Dictator(_DictatorSignals):
    """Reads the given text aloud using the OS's text-to-speech APIs.

    Also supports pausing and notifying the caller which word is currently
    being spoken.

    TODO: Implement notifying the caller about which word was spoken.

    TODO: Discuss the different strategies used to speak for slow and fast
    words.
    """

    started_dictation = pyqtSignal()
    """Emitted when the dictation has actually started.

    There may be a delay between the user pressing the "start" button and the
    dictation actually starting. We would like to updated GUI to let the user
    know that the dictation is starting, even if they can't hear anything yet.
    But then we have to know when the dictation has actually started, so that
    we can undo our update to the GUI.
    """

    def __init__(self, parent):
        """Initialize to dictate the given text.

        :param QObject parent: The parent of this QObject.
        """
        # No parent for self. We can't move the worker to a different thread if
        # it has a parent, because the thread takes ownership of the worker.
        super(Dictator, self).__init__()

        # Instead, tie the lifetime of the thread itself to the provided
        # parent.
        self._thread = QThread(parent)

        self.moveToThread(self._thread)
        self.done.connect(self._on_done)

        self._stop_pumping = threading.Event()
        self._loop_thread = None

        # Note: the text-to-speech engine takes about a second to initialize
        # (on my macOS machine). Thus, we initialize it in advance, then pass
        # it to the dictation strategy when we actually need to dictate.
        self._engine = pyttsx.init(debug=True)
        self._start_loop()

        self._strategy = None
        self._has_started_dictation = False

    def start(self, text, rate):
        """Start dictating the given text.

        :param str text: The text to be spoken.
        :param int rate: The rate at which to speak the text, in words per
            minute.
        """
        assert text, "No text to dictate was provided."
        assert 1 <= rate <= 999, (
            "Speech rate is not in a reasonable range (was {} wpm)"
            .format(rate))

        if rate >= _FAST_DICTATION_CUTOFF:
            self._strategy = _FastDictator(engine=self._engine,
                                           text=text,
                                           rate=rate)
        else:
            raise NotImplementedError()

        self._strategy.done.connect(self.done)
        self._strategy.started_word.connect(self.started_word)

        # When this is written as a method, the function never seems to be
        # called, for some reason.
        def _on_started_word(_index):
            # The dictation has started once the first word has been said.
            if not self._has_started_dictation:
                self._has_started_dictation = True
                self.started_dictation.emit()
        self._strategy.started_word.connect(_on_started_word)

        self._strategy.start()

    def stop(self):
        """Stop dictation of the text.

        This is different from pausing in that the dictation can't be resumed.
        It also takes longer to stop than it does to pause.
        """
        if self._strategy:
            self._strategy.stop()
        self._stop_pumping.set()
        self._loop_thread.join()
        try:
            self._engine.endLoop()
        except RuntimeError:
            # The engine wasn't running, no problem.
            pass
        self._thread.quit()

    def pause(self):
        """Pause in the middle of the current word."""
        self._strategy.pause()

    def resume(self):
        """Resume speaking after having paused."""
        self._strategy.resume()

    def _start_loop(self):
        """Start the event loop in the background."""
        def run_loop():
            while not self._stop_pumping.wait(_EVENT_LOOP_INTERVAL):
                self._engine.iterate()

        self._loop_thread = threading.Thread(target=run_loop)
        self._loop_thread.start()
        self._engine.startLoop(useDriverLoop=False)

    def _on_done(self):
        assert self._loop_thread, (
            "The dictation somehow ended without there being an active event "
            "loop thread.")
        self.stop()


class _FastDictator(_DictatorSignals):
    """Dictate by just delegating the entire text to the engine."""

    def __init__(self, engine, text, rate):
        super(_FastDictator, self).__init__()
        self._engine = engine
        self._text = text
        self._rate = rate

    def start(self):
        self._engine.connect("started-word", self._started_word)
        self._engine.connect("finished-utterance", self._finished_utterance)

        self._engine.setProperty("rate", self._rate)
        self._engine.say(self._text)

    def _started_word(self, name, location, length):
        self.started_word.emit(0)

    def _finished_utterance(self, name, completed):
        if completed:
            self.done.emit()

    def stop(self):
        self._engine.stop()

    def pause(self):
        raise NotImplementedError()

    def resume(self):
        raise NotImplementedError()
