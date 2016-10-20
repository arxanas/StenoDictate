"""The main window for the application."""
import logging

from PyQt5.QtWidgets import QDialog, QMainWindow, QMessageBox

from stenodictate.gui.importtext import ImportTextDialog
from stenodictate.gui.mainwindow_ui import Ui_MainWindow
from stenodictate.state import Library


class MainWindow(QMainWindow, Ui_MainWindow):
    """The main window for the application."""

    def __init__(self):
        """Construct the window."""
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.action_import.triggered.connect(self.import_text)

    def import_text(self):
        """Import a (in a .txt file) into the user's library."""
        dialog = ImportTextDialog()
        if dialog.exec_() != QDialog.Accepted:
            return

        try:
            library = Library.from_app_state()
            library.add_text(title=dialog.title, path=dialog.file_path)
        except IOError as e:
            logging.exception("Import failure for file: {}"
                              .format(dialog.file_path))
            QMessageBox.critical(
                self,
                "Import failure",
                "Could not import text. Error message: {}".format(e.message),
            )
