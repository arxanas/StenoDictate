"""Main entry point to launch the app."""
import sys

from PyQt5.QtWidgets import qApp, QApplication

from stenodictate.gui.crashwindow import CrashWindow
from stenodictate.gui.mainwindow import MainWindow


def main():
    """Launch the GUI app.

    If an unhandled exception is raised during the execution of the program, a
    friendly crash window is shown.
    """
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    def show_crash_window(type, value, traceback):
        """In the event of any crash, display a friendlier message."""
        # https://riverbankcomputing.com/pipermail/pyqt/2009-May/022961.html
        main_window.close()
        crash_window = CrashWindow(type, value, traceback)
        crash_window.exec_()
        qApp.quit()
    sys.excepthook = show_crash_window

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
