"""Let the user select a dictation text to import."""
import os.path

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from stenodictate.gui.importtext_ui import Ui_ImportTextDialog


class ImportTextDialog(QDialog, Ui_ImportTextDialog):
    """The dialog to import a text into the library."""

    @property
    def file_path(self):
        """The full path to the selected text file."""
        return self._file_path

    @property
    def title(self):
        """The title of the dictation text."""
        return self.titleLineEdit.text().strip()

    def __init__(self):
        """Initialize the dialog."""
        super(ImportTextDialog, self).__init__()
        self.setupUi(self)

        self._file_path = None

        self.selectFileButton.clicked.connect(self._set_file)
        self.buttons.accepted.connect(self._validate)

    def _set_file(self):
        self._file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Import text",
            directory=None,
            filter="*.txt",
        )
        self.filename.setText(os.path.basename(self._file_path))

    def _validate(self):
        """Validate the form."""
        MESSAGEBOX_TITLE = "Cannot add text"
        if not self.title:
            QMessageBox.critical(
                self,
                MESSAGEBOX_TITLE,
                "You must enter a title for this dictation text.",
            )
            return
        elif not self.file_path:
            QMessageBox.critical(
                self,
                MESSAGEBOX_TITLE,
                "You must select a dictation text file.",
            )
            return

        self.accept()
