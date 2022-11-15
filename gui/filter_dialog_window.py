import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from gui import utils as ut


class FilterDialog(QDialog):

    def __init__(self, comment: str) -> None:
        """
        :param comment: initial comment fot filter.
        """

        super().__init__()
        self._comment: str = comment
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Method initializes widgets on dialog window.
        """

        loadUi(os.path.join(ut.DIR_MEDIA, "filter_params_dialog_window.ui"), self)
        self.setWindowTitle("Настройки фильтра")
        self.setWindowIcon(QIcon(os.path.join(ut.DIR_MEDIA, "icon.png")))
        self.line_edit_comment.setText(self._comment)
        self.line_edit_comment.returnPressed.connect(self.accept)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)

    def get_comment(self) -> str:
        """
        Method returns text in line edit.
        :return: comment.
        """

        return self.line_edit_comment.text()
