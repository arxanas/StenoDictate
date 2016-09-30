"""Dictate text to the by pausing between words as necessary.

It's easy to ask a text-to-speech engine to speak at a given word rate.
However, this is often problematic, because at low speeds, the engine will just
slow down the text to the point of unintelligibility.

Human dictators will speak at a natural pace, but pause in between words as
necessary to reach the given word rate. This module tries to approximate that
by starting and stopping the text-to-speech engine to pause between words.
"""
import sys
import time

import pyttsx
from textstat.textstat import textstat

MIN_RATE = 100
"""The minimum word rate to actually speak at."""

NUM_WORDS_PER_SYLLABLE = 1.0 / 1.44
"""This number was derived from a brochure about the EV360 software."""


def dictate(text, rate):
    """Dictate text at the given rate, pausing between words as necessary.

    :param str text: The text to dictate.
    :param int rate: A word rate, in words per minute.
    """
    text = text.strip()
    start_time = time.time()

    if rate <= 0:
        raise ValueError("Word rate must be positive!")

    class outer:
        """Dumb hack because Python sucks.

        See http://stackoverflow.com/q/3190706/344643.
        """

        location = 0
        """The location (as an index) we're at in the overall text.

        This is calculated and updated as we continue reading through the
        words.
        """

        base_location = 0
        """The location from which we resumed talking.

        When the engine gives us parameters in the callback, they're relative
        to the text that we provided the engine. Since the text was created by
        slicing the words we've already spoken off the original text, the
        offsets that it provides as parameters will be relative to that
        shorter, sliced text, and not the original text.

        So whenever we stop talking, we store the "base location", which is
        where we're about to resume the next part of the text. Then, given the
        offsets as parameters, we can calculate our actual location in the
        text.
        """

        previous_word = None
        previous_words = []

        done_dictating = False

    def word_rate_so_far():
        current_time = time.time()
        time_elapsed = current_time - start_time
        num_minutes_so_far = time_elapsed / 60.0

        if not num_minutes_so_far:
            # If in the unlikely event the clock time hasn't changed between
            # the time we set `start_time` and the time that we first ran this
            # function, avoid having a division by zero error below. I'm not
            # sure that this can actually happen on a real system, but it
            # doesn't hurt.
            return

        assert all(word for word in outer.previous_words)
        num_syllables_so_far = sum(textstat.syllable_count(word)
                                   for word in outer.previous_words)

        num_words_so_far = num_syllables_so_far * NUM_WORDS_PER_SYLLABLE
        return num_words_so_far / num_minutes_so_far

    def register_word_spoken(location, length):
        # On the first invocation, we don't have a previous word.
        if outer.previous_word is not None:
            # Don't add punctation, spacing, etc.
            if any(c.isalpha() for c in outer.previous_word):
                outer.previous_words.append(outer.previous_word)

        location += outer.base_location
        outer.previous_word = text[location:location + length]

    def pause_if_necessary(location, length):
        outer.location = outer.base_location + location

        # `word_rate_so_far` looks at the current clock time, so eventually
        # we should resume speaking, when enough time has elapsed that our
        # word rate is suitably low.
        #
        # Couldn't we determine exactly how long we actually have to sleep
        # in order to fall under the desired word rate? Only if you are
        # less lazy of an engineer than I am.
        while word_rate_so_far() > rate:
            if engine.isBusy():
                # Let the engine finish the syllable it's on. Not exactly
                # foolproof.
                time.sleep(0.1)
                engine.stop()
            time.sleep(0.01)

    def on_word(name, location, length):
        try:
            register_word_spoken(location, length)
            pause_if_necessary(location, length)
        except Exception:
            # Exceptions that occur in a callback seem to be swallowed
            # silently, so manually report any exceptions.
            import traceback
            traceback.print_exc()
            engine.stop()

    def on_finish(name, completed):
        # If the utterance stopped because the engine was interrupted (that is,
        # `completed == False`), don't actually stop the dictation loop.
        if completed:
            outer.done_dictating = True

    engine = pyttsx.init()
    engine.setProperty("rate", max(rate, MIN_RATE))
    engine.connect("started-word", on_word)
    engine.connect("finished-utterance", on_finish)

    while not outer.done_dictating:
        # Resume (or start, it doesn't matter) our speech from the point we
        # used to be at.
        outer.previous_word = None
        outer.base_location = outer.location
        engine.say(text[outer.location:])
        engine.runAndWait()


def main():
    text = sys.stdin.read()
    dictate(text, rate=40)

if __name__ == "__main__":
    main()
