"""Dictate text to the by pausing between words as necessary.

It's easy to ask a text-to-speech engine to speak at a given word rate.
However, this is often problematic, because at low speeds, the engine will just
slow down the text to the point of unintelligibility.

Human dictators will speak at a natural pace, but pause in between words as
necessary to reach the given word rate. This module tries to approximate that
by pausing the text-to-speech engine between words.
"""
import logging
import sys
import threading
import time

import pyttsx
from textstat.textstat import textstat

SLOW_DICTATION_RATE = 260
"""The speed at which to dictate individual words in slow dictation."""

FAST_DICTATION_CUTOFF = 140
"""The speed, in wpm, at which to stop pronouncing words individually."""

NUM_WORDS_PER_SYLLABLE = 1.0 / 1.44
"""This number was derived from a brochure about the EV360 software."""

PUNCTUATION_PAUSES = {
    ".": 1.0,
    "?": 1.0,
    "!": 1.0,
    ";": 1.0,
    ":": 1.0,
    ",": 0.75,
}
"""The fraction of a word-length to pause after punctuation."""

DEFAULT_RATE = 180
"""The word rate to dictate at, if no rate is given.

This only applies when the module is invoked as a script.
"""


def dictate(text, rate):
    """Dictate text at the given rate.

    If the rate is too slow, the dictator will pause between words to preserve
    intelligibility.

    :param str text: The text to dictate.
    :param int rate: A word rate, in words per minute.
    """
    text = text.strip()

    if rate <= 0:
        raise ValueError("Word rate must be positive!")
    if not text:
        raise ValueError("Must have at least one word to dictate!")

    if rate >= FAST_DICTATION_CUTOFF:
        _dictate_fast(text, rate)
    else:
        _dictate_slow(text, rate)


def _dictate_slow(text, rate):
    """Dictate text slowly, with pauses between words.

    The actual speech will be spoken at a much faster rate, but there will be a
    pause between each word so that the user can stroke it.
    """
    words = text.split()
    word_timings = list(_schedule_words(text, rate))

    # Engine init takes about a second to start up, so make sure to only start
    # recording the time after that.
    engine = pyttsx.init()
    start_time = time.time()

    lock = threading.Lock()
    stop_flag = threading.Event()

    class outer(object):
        num_pending_words = 0
        num_ticks_of_lag = 0

        previous_location = 0
        """Used to determine when a word has finished being spoken."""

        current_word = 0
        """The index of the word currently being spoken."""

    def get_timestamp():
        """Get the number of seconds since we started dictation."""
        return time.time() - start_time

    def say_words():
        for i, word in enumerate(words):
            with lock:
                outer.current_word = i
                if stop_flag.is_set():
                    return

                # Determine the pause we need for the next word.
                try:
                    scheduled_time = word_timings[i + 1]
                except IndexError:
                    scheduled_time = 0

                logging.debug("Saying word: {}".format(word))
                outer.num_pending_words += 1

            if i < len(words) - 1:
                engine.say(word)
            else:
                engine.say(word, "final")

            if scheduled_time:
                pause_time = scheduled_time - get_timestamp()
                if pause_time > 0:
                    stop_flag.wait(pause_time)

    def on_word(name, location, length):
        """If the speech engine is falling behind, give it extra time."""
        with lock:
            # We can't directly determine if this is a new word or not, so
            # determine it by seeing if we've started the beginning of a
            # different word.
            #
            # One approach that doesn't work is checking if the location is
            # zero, because punctation like quotation marks aren't pronounced.
            # But those punctuation marks might be at the beginning of the
            # utterance, so the engine would start at a location greater than
            # zero.
            old_previous_location = outer.previous_location
            outer.previous_location = location
            if location > old_previous_location:
                return

            outer.num_pending_words -= 1
            if outer.num_pending_words:
                outer.num_ticks_of_lag += 1
                logging.debug("Num pending words: {}"
                              .format(outer.num_pending_words))
            else:
                outer.num_ticks_of_lag = 0

            # If we've had pending words for the last few ticks, give the
            # speech engine a rest and allow it to say words a little bit
            # later.
            if outer.num_ticks_of_lag >= 3:
                current_time = get_timestamp()
                next_word_time = word_timings[outer.current_word]
                time_difference = current_time - next_word_time
                time_difference += 0.5
                if time_difference <= 0:
                    return

                word_timings[:] = [round(timing + time_difference, 2)
                                   for timing in word_timings]
                logging.debug("Giving speech engine {:.2f} seconds"
                              .format(time_difference))
                logging.debug("Current time is {:.2f}; next few times are {}"
                              .format(
                    current_time,
                    word_timings[outer.current_word:outer.current_word + 5]
                ))

    def on_end(name, completed):
        if completed and name == "final":
            engine.stop()
            engine.endLoop()

    engine.setProperty("rate", SLOW_DICTATION_RATE)
    engine.connect("started-word", on_word)
    engine.connect("finished-utterance", on_end)
    speech_thread = threading.Thread(target=say_words)
    speech_thread.start()
    try:
        engine.startLoop()
    except KeyboardInterrupt:
        stop_flag.set()
        speech_thread.join()
    finally:
        try:
            engine.endLoop()
        except RuntimeError:
            # It was already ended, nothing to do here.
            pass


def _dictate_fast(text, rate):
    """Dictate the text, without doing anything special."""
    engine = pyttsx.init()
    engine.setProperty("rate", rate)
    engine.say(text)
    engine.runAndWait()


def _schedule_words(text, rate):
    """Determine the time at which to speak each word for slow dictation.

    :returns list: A list of floats, starting from 0 and monotonically
    increasing, corresponding to the time at which to say each word.
    """
    num_syllables = textstat.syllable_count(text)
    total_dictation_time = num_syllables * NUM_WORDS_PER_SYLLABLE / rate
    total_dictation_seconds = total_dictation_time * 60.0

    words = text.split()
    time_per_word = total_dictation_seconds / len(text.split())

    current_time = 0.0
    for word in words:
        # There's no technical reason to round, it's just nice to not have to
        # worry about making a pretty string representation of the list of
        # timings.
        yield round(current_time, 2)

        word_length = time_per_word
        punctuation_pause = PUNCTUATION_PAUSES.get(word[-1])
        if punctuation_pause:
            word_length += time_per_word * punctuation_pause
        current_time += word_length


def main():
    logging.basicConfig(level=logging.DEBUG)
    text = sys.stdin.read()

    rate = DEFAULT_RATE
    for i, j in zip(sys.argv, sys.argv[1:]):
        if i == "-r":
            rate = int(j)

    dictate(text, rate=rate)

if __name__ == "__main__":
    main()
