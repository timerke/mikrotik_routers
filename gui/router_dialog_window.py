import os
from enum import auto, Enum
from typing import Dict, List
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QComboBox, QDialog, QLayout
from gui import utils as ut


class DialogMode(Enum):
    ALL = auto()
    SINGLE = auto()


class RouterDialog(QDialog):
    """
    Class to change parameters for router.
    """

    data_should_be_send: pyqtSignal = pyqtSignal()
    new_data_should_be_set: pyqtSignal = pyqtSignal(dict, list)

    def __init__(self) -> None:
        super().__init__()
        self._default_data: Dict[str, str] = {}
        self._mode: DialogMode = None
        self._routers: List[Dict[str, str]] = []
        self._router_ip_address: str = ""
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Method initializes widgets on dialog window.
        """

        loadUi(os.path.join(ut.DIR_MEDIA, "router_params_dialog_window.ui"), self)
        self.setWindowTitle("Настройки коммутаторов")
        self.setWindowIcon(QIcon(os.path.join(ut.DIR_MEDIA, "icon.png")))
        self._set_default_user_and_password()
        self.combo_box_ip_addresses.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_box_ip_addresses.lineEdit().setReadOnly(True)
        self.combo_box_ip_addresses.currentTextChanged.connect(self.set_params_for_router)
        self._set_routers_data()
        self.button_ok.clicked.connect(self.change_data)
        self.button_cancel.clicked.connect(self.close)

    def _set_default_user_and_password(self) -> None:
        """
        Method sets default user name and password to widgets.
        """

        self.line_edit_default_user_name.setText(self._default_data.get("user", ""))
        self.line_edit_default_password.setText(self._default_data.get("password", ""))

    def _set_routers_data(self) -> None:
        """
        Method sets routers data to widgets.
        """

        ip_addresses = [str(router.get("ip_address", "")) for router in self._routers]
        self.combo_box_ip_addresses.clear()
        self.combo_box_ip_addresses.addItems(ip_addresses)
        self.group_box_router.setEnabled(bool(self._routers))

    @pyqtSlot()
    def change_data(self) -> None:
        """
        Method changes default user name and password and routers data.
        """

        self._default_data = {"user": self.line_edit_default_user_name.text(),
                              "password": self.line_edit_default_password.text()}
        for router in self._routers:
            if str(router.get("ip_address", "")) == self.combo_box_ip_addresses.currentText():
                router["user"] = self.line_edit_user_name.text() if self.line_edit_user_name.text() else None
                router["password"] = self.line_edit_password.text() if self.line_edit_password.text() else None
                break
        self.new_data_should_be_set.emit(self._default_data, self._routers)
        self.close()

    @pyqtSlot(dict, list)
    def set_new_data(self, default_data: Dict[str, str], routers: List[Dict[str, str]]) -> None:
        """
        Slot sets new data for default user name and password and routers data.
        :param default_data: dictionary with default user name and password;
        :param routers: list with routers data.
        """

        self._default_data = default_data
        self._routers = routers
        self._set_default_user_and_password()
        self._set_routers_data()
        if self._mode is DialogMode.SINGLE:
            self.combo_box_ip_addresses.setCurrentText(self._router_ip_address)

    @pyqtSlot(str)
    def set_params_for_router(self, router_ip_address: str) -> None:
        """
        Slot sets user name and password for router in widgets.
        :param router_ip_address: IP address of router.
        """

        user = ""
        password = ""
        for router in self._routers:
            if router_ip_address == str(router.get("ip_address", "")):
                user = router.get("user", self._default_data.get("user", ""))
                password = router.get("password", self._default_data.get("password", ""))
                break
        self.line_edit_user_name.setText(user)
        self.line_edit_password.setText(password)

    def show_mode(self, mode: DialogMode, router_ip_address: str) -> None:
        """
        Method shows dialog window in given mode.
        :param mode: mode of dialog window;
        :param router_ip_address: IP address of current router.
        """

        self._mode = mode
        self._router_ip_address = router_ip_address
        self.group_box_default.setVisible(mode is DialogMode.ALL)
        self.combo_box_ip_addresses.setEnabled(mode is DialogMode.ALL)
        self.setFixedSize(self.sizeHint())
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.exec()
