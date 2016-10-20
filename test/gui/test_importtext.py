from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialogButtonBox

from stenodictate.gui.importtext import ImportTextDialog


def test_importtext(app):
    dialog = ImportTextDialog()
    dialog.show()

    QTest.keyClicks(dialog.title_lineedit, "foo")
    dialog._file_path = "foo"
    QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.Ok), Qt.LeftButton)
