"""The library is the user's collection of texts to be dictated.

In order to have the app dictate a text, it must first be imported into the
library. This is so that we can keep our own copies of the text and store
analytics later, even if the user modifies or details their copy of the text.
"""
import collections
import shutil

import py.path
from PyQt5.QtCore import pyqtSignal, QObject, QVariant
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from stenodictate.state import app_state


class DictationText(collections.namedtuple("DictationText", "title path")):
    """A text stored on disk for dictation to the user."""

    def get_text(self):
        """Read the contents of the text file backing this dictation text.

        :raises EnvironmentError: Something unusual happened, like the file not
            existing or being readable.
        """
        return py.path.local(self.path).read()


class Library(object):
    """Stores the user's library on disk."""

    _LIBRARY_DIR = "library"
    """The directory in which to store the user's texts."""

    def __init__(self, app_state):
        """Private. Construct from the given app state."""
        self._app_state = app_state
        self._init_app_state()

    @classmethod
    def from_app_state(cls):
        """Construct the library for the current instance of the app."""
        return cls(app_state)

    def _init_app_state(self):
        """Initialize the schema for the library state."""
        if self._app_state["library"] is not None:
            return

        self._app_state["library"] = {
            "next_file_id": 1,
            "texts": [],
        }

    def _get_file_path_for_text(self, text_basename):
        """Determine the path to save the given dictation text.

        :param str text_basename: The basename of a text file, like
            "text-1.txt".
        :returns py.path.local: The path to save the file. All intermediate
            directories have been created.
        """
        path = self._app_state.app_dir.join(self._LIBRARY_DIR)
        path.ensure_dir()
        path = path.join(text_basename)
        assert not path.check(), (
            "The file path '{}' for an imported dictation text already "
            "existed, but this should not have happened because it should "
            "have been given a unique ID.".format(text_basename)
        )
        return path

    def add_text(self, title, path):
        """Copy a dictation text into the library.

        :param str title: The human-readable title of this text.
        :param str path: The path to the file on disk. This file is then copied
            into the app state.
        :raises IOError: The file could not be copied into the library.
        """
        assert title
        assert path

        state = self._app_state["library"]
        filename = "text-{}.txt".format(state["next_file_id"])
        state["next_file_id"] += 1

        try:
            target_path = self._get_file_path_for_text(filename)
            shutil.copyfile(path, str(target_path))

            text = DictationText(title=title, path=str(target_path))
            state["texts"].append(text)
            return text
        finally:
            # Make sure to increment the next file ID, just in case the file
            # was partially written but threw an Error, or something like that.
            self._app_state["library"] = state

    def get_texts(self):
        """Get a list of all the texts in the library.

        :returns list: A list of DictationText objects.
        """
        return self._app_state["library"]["texts"]


class LibraryModel(QObject):
    """A QStandardModel wrapper.

    :ivar QStandardModel model: The model containing the texts.
    """

    text_added = pyqtSignal(DictationText)
    """Should be emitted when a text is added to the library."""

    @property
    def qt_model(self):
        """Get the underlying QStandardItemModel."""
        return self._model

    def __init__(self, library, list_view):
        """Initialize the model to contain the texts in the library."""
        super(LibraryModel, self).__init__()
        self._library = library
        self._list_view = list_view

        self._model = QStandardItemModel()
        self._populate()

        self.text_added.connect(self._on_text_added)

    def _populate(self):
        for text in self._library.get_texts():
            self._model.appendRow(self._create_item(text))

    def _create_item(self, text):
        item = QStandardItem(text.title)
        item.setEditable(False)
        item.setData(QVariant(text))
        return item

    def _on_text_added(self, text):
        item = self._create_item(text)
        self._model.appendRow(item)
        self._list_view.setCurrentIndex(self._model.indexFromItem(item))
