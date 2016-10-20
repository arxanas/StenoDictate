"""Underlying layer to persist application state.

This module exposes an interface to access data for specific "keys". Each
distinct part of the application stores its data in its own key, and maintains
that key's schema. The various parts of the application thus wrap this class in
some way.
"""
import cPickle as pickle

import appdirs
import py.path

from stenodictate import __version__ as version


class State(object):
    """Persists state on disk by pickling.

    The user gives this class a key, which can be used to look up or save a
    piece of picklable data. The data for this key is stored in a file in the
    user's data directory. The data is also versioned with the current version
    of the app, although the user can't see this.

    Thus, the class actually stores a dict like this for every piece of data:

        {
            "version": "1.0",
            "data": ...,
        }

    This might be useful in the future.
    """

    _APP_NAME = "StenoDictate"
    """The app name to use when determining the directory to store data."""

    _STATE_DIR = "state"
    """The directory to store the pickle files in."""

    @property
    def app_dir(self):
        """The directory in which the app data files are to be stored in.

        :returns py.path.local: The parent of the directory that stores the
            state files. It is suitable for use by other part of the
            application.
        """
        assert self._has_inited, (
            "Tried to get app data directory before initialization of app "
            "state. This is a problem because the app data directory is "
            "determined during initialization. Make a call to read or write "
            "some app state first, or initialize manually."
        )
        return self._app_dir

    def __init__(self):
        """Prepare to read and write the application state.

        Doesn't access the disk until the first actual attempt to read or write
        data.
        """
        self._has_inited = False

    def _init(self, app_dir=None):
        """Create the directory structure on disk.

        :param str app_dir: The root directory for the application state. If
            not given, uses the default data directory for the current OS.
        """
        self._has_inited = True

        if not app_dir:
            app_dir = appdirs.user_data_dir(appname=self._APP_NAME)
        self._app_dir = py.path.local(app_dir)

        self._state_dir = self._app_dir.join(self._STATE_DIR)
        self._state_dir.ensure_dir()

    def _get_file_for_key(self, key):
        assert all(c.isalpha() for c in key), "Invalid key for state"
        return self._state_dir.join(key)

    def __getitem__(self, key):
        """Get the application state associated with the given key.

        :param str key: The name of the piece of state being read.
        :returns object: Returns whatever data was stored for this key
            (probably a dict), or None if this key has never been written to
            before.
        """
        if not self._has_inited:
            self._init()

        key_file = self._get_file_for_key(key)
        if not key_file.check(file=1):
            return None

        with key_file.open() as f:
            data = pickle.load(f)
            return data["data"]

    def __setitem__(self, key, value):
        """Write data for a given key.

        :param str key: The name of the piece of state being written.
        :param object value: A picklable object, probably a dictionary.
        """
        if not self._has_inited:
            self._init()

        key_file = self._get_file_for_key(key)
        with key_file.open("w", ensure=True) as f:
            data = {
                "version": version,
                "data": value,
            }
            pickle.dump(data, f)


app_state = State()
