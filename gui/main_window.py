import ipaddress
import logging
import os
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QRegExp, QThread
from PyQt5.QtGui import QCloseEvent, QIcon, QRegExpValidator
from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
from gui import utils as ut
from gui.filter_table import FilterTable
from gui.log_table import LogTable
from gui.logger import LoggingHandler
from mikrotik.config_data import ConfigData


logger = logging.getLogger()
formatter = logging.Formatter("[%(asctime)s - %(levelname)s] %(message)s")
logging_forwarder = LoggingHandler()
logging_forwarder.setLevel(logging.INFO)
logging_forwarder.setFormatter(formatter)
logger.addHandler(logging_forwarder)


class MainWindow(QMainWindow):
    """
    Class for main window of application.
    """

    mac_address_should_be_added: pyqtSignal = pyqtSignal(str, str)
    router_ip_address_should_be_added: pyqtSignal = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.filter_table: FilterTable = FilterTable()
        self.log_table: LogTable = LogTable()
        self._config_data: ConfigData = ConfigData()
        self._thread: QThread = QThread(parent=self)
        self._thread.setTerminationEnabled(True)
        self._config_data.moveToThread(self._thread)
        self._thread.start()
        self._init_ui()
        self._connect_signals()
        self._default_line_edit_style_sheet: str = self.line_edit_mac_address.styleSheet()

    def _check_ip_address(self) -> bool:
        """
        Method checks that IP address is correct.
        :return: True if IP address if correct.
        """

        if not self.line_edit_router_ip_address.hasAcceptableInput():
            return False
        try:
            ipaddress.ip_address(self.line_edit_router_ip_address.text())
        except ValueError:
            return False
        return True

    def _connect_signals(self) -> None:
        """
        Method to connect all signals between different objects.
        """

        logging_forwarder.log_received.connect(self.log_table.add_log)
        self.filter_table.filter_should_be_added.connect(self._config_data.add_filter_to_router)
        self.filter_table.filter_should_be_changed.connect(self._config_data.change_filter_state)
        self.filter_table.filter_should_be_deleted.connect(self._config_data.delete_filter_from_router)
        self.filter_table.router_should_be_deleted.connect(self._config_data.delete_router)
        self.filter_table.table_should_be_updated.connect(self._config_data.get_statistics)
        self.filter_table.table_should_be_updated.connect(lambda: self.enable_widgets(False))
        self.mac_address_should_be_added.connect(self.filter_table.add_filter_to_table)
        self._config_data.router_ip_address_added.connect(self.filter_table.send_signal_to_update_table)
        self._config_data.statistics_finished.connect(lambda: self.enable_widgets(True))
        self._config_data.statistics_received.connect(self.filter_table.add_statistics)
        self.router_ip_address_should_be_added.connect(self._config_data.add_ip_address)
        self._thread.finished.connect(self._config_data.save)
        self.filter_table.send_signal_to_update_table()

    def _init_ui(self) -> None:
        """
        Method initializes widgets on main window.
        """

        loadUi(os.path.join(ut.DIR_MEDIA, "main_window.ui"), self)
        self.setWindowTitle("MiFiSToFEL")
        self.setWindowIcon(QIcon(os.path.join(ut.DIR_MEDIA, "icon.png")))
        self.vertical_layout_for_filter_table.addWidget(self.filter_table)
        self.vertical_layout_for_log_table.addWidget(self.log_table)

        mac_address_validator = QRegExpValidator(QRegExp(r"^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2}) (SRC|src|DST|dst)$"))
        self.line_edit_mac_address.setValidator(mac_address_validator)
        self.line_edit_mac_address.returnPressed.connect(self.add_mac_address)
        self.line_edit_mac_address.textChanged.connect(self.check_line_edit)
        self.button_add_mac_address.clicked.connect(self.add_mac_address)
        ip_address_validator = QRegExpValidator(QRegExp(r"^(\d{1,3}\.){3}(\d{1,3})$"))
        self.line_edit_router_ip_address.setValidator(ip_address_validator)
        self.line_edit_router_ip_address.returnPressed.connect(self.add_router_ip_address)
        self.line_edit_router_ip_address.textChanged.connect(self.check_line_edit)
        self.button_add_router_ip_address.clicked.connect(self.add_router_ip_address)

        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 4)

    @pyqtSlot()
    def add_mac_address(self) -> None:
        """
        Slot to add new MAC address to filter table.
        """

        if self.line_edit_mac_address.hasAcceptableInput():
            mac_address, target = self.line_edit_mac_address.text().split()
            self.mac_address_should_be_added.emit(mac_address.upper(), target.upper())

    @pyqtSlot()
    def add_router_ip_address(self) -> None:
        """
        Slot to add new IP address of switch to filter table.
        """

        if self._check_ip_address():
            self.router_ip_address_should_be_added.emit(self.line_edit_router_ip_address.text())

    @pyqtSlot()
    def check_line_edit(self) -> None:
        """
        Slot checks content of line edit.
        """

        if self.sender() is self.line_edit_router_ip_address:
            acceptable_input = self._check_ip_address()
        else:
            acceptable_input = self.sender().hasAcceptableInput()
        if acceptable_input or not self.sender().text():
            self.sender().setStyleSheet(self._default_line_edit_style_sheet)
            self.sender().setToolTip("")
        else:
            self.sender().setStyleSheet("border: 1px solid red;")
            self.sender().setToolTip("Введите IP адрес в формате xxx.xxx.xxx.xxx"
                                     if self.sender() is self.line_edit_router_ip_address else
                                     "Введите MAC адрес в формате xx:xx:xx:xx:xx:xx SRC|DST")

    def closeEvent(self, close_event: QCloseEvent) -> None:
        """
        Method handles main window closing.
        :param close_event: close event.
        """

        self._thread.quit()
        super().closeEvent(close_event)

    @pyqtSlot(bool)
    def enable_widgets(self, enable: bool) -> None:
        """
        Slot enables or disables widgets.
        :param enable: if True widgets will be enabled.
        """

        for widget in (self.filter_table, self.button_add_mac_address, self.button_add_router_ip_address,
                       self.line_edit_mac_address, self.line_edit_router_ip_address):
            widget.setEnabled(enable)
