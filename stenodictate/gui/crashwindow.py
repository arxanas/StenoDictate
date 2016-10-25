"""Display an unhandled exception upon program crash."""
import time
import traceback

from PyQt5.QtWidgets import QDialog

from stenodictate import __version__ as version
from stenodictate.gui.crashwindow_ui import Ui_CrashWindow


class CrashWindow(QDialog, Ui_CrashWindow):
    """Display information about the raised exception."""

    def __init__(self, type, value, traceback_):
        """Initialize the window with the exception information."""
        super(CrashWindow, self).__init__()
        self.setupUi(self)

        message = """
StenoDictate version: {version}
Timestamp: {time}
{traceback}
""".strip().format(
            time=time.time(),
            version=version,
            traceback="\n".join(
                traceback.format_exception(type, value, traceback_))
        )

        self.errorMessage.setText(message)
