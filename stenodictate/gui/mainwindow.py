"""The main window for the application."""
import logging

from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QDialog, QMainWindow, QMessageBox

from stenodictate.gui.importtext import ImportTextDialog
from stenodictate.gui.mainwindow_ui import Ui_MainWindow
from stenodictate.qdictate import Dictator
from stenodictate.state.library import Library, LibraryModel


class MainWindow(QMainWindow, Ui_MainWindow):
    """The main window for the application."""

    def __init__(self):
        """Construct the window."""
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self._library = Library.from_app_state()
        self._library_model = LibraryModel(self._library, self.libraryListView)
        self.libraryListView.setModel(self._library_model.qt_model)

        self.actionImport.triggered.connect(self._import_text)
        self.libraryListView.selectionModel() \
            .selectionChanged.connect(self._text_changed)

        self._dictation_document = QTextDocument(self.dictationTextEdit)
        self.dictationTextEdit.setDocument(self._dictation_document)

        self._dictator = Dictator(parent=self)
        self.startDictationButton.clicked.connect(self._start_dictation)

    def closeEvent(self, event):
        """Stop the dictation if it's still in progress."""
        if self._dictator:
            self._dictator.stop()

    def _import_text(self):
        """Import a (in a .txt file) into the user's library."""
        dialog = ImportTextDialog()
        if dialog.exec_() != QDialog.Accepted:
            return

        try:
            text = self._library.add_text(title=dialog.title,
                                          path=dialog.file_path)
            self._library_model.text_added.emit(text)
        except IOError as e:
            logging.exception("Import failure for file: {}"
                              .format(dialog.file_path))
            QMessageBox.critical(
                self,
                "Import failure",
                "Could not import text. Error message: {}".format(e.message),
            )

    def _select_added_text(self, text):
        last_index = len(self._library.get_texts()) - 1
        self.libraryListView.setCurrentIndex(last_index)

    def _text_changed(self, selection):
        index = selection.indexes()[0]
        text = self._library_model.qt_model.itemFromIndex(index).data()
        self._dictation_document.setPlainText(text.get_text())

    def _start_dictation(self):
        current_text = self._get_current_text()
        if not current_text:
            QMessageBox.critical(
                self,
                "Cannot dictate",
                "Select a text from the left to dictate.",
            )
            return

        word_rate = self.wpmSpinBox.value()

        self.startDictationButton.setDisabled(True)
        self.startDictationButton.setText("Starting...")

        def started_dictation():
            # TODO: Actually do something when the user presses this new
            # button.
            self.startDictationButton.setText("Started")

        self._dictator.started_dictation.connect(started_dictation)
        self._dictator.start(text=current_text, rate=word_rate)

    def _get_current_text(self):
        try:
            index = self.libraryListView.selectionModel().selectedIndexes()[0]
        except IndexError:
            return None

        data = self._library_model.qt_model.itemFromIndex(index).data()
        return data.get_text()
