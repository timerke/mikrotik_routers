import os
from typing import Dict, List
from PyQt5.QtCore import QCoreApplication, pyqtSlot, QPoint, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog, QHeaderView, QLabel, QMenu, QTableWidget
from gui import utils as ut


class LogTable(QTableWidget):
    """
    Class for table widget to display logs.
    """

    _COLORS_FOR_LOGS: Dict[str, str] = {"CRITICAL": "red",
                                        "DEBUG": "black",
                                        "ERROR": "red",
                                        "INFO": "blue",
                                        "UNKNOWN": "pink",
                                        "WARN": "orange",
                                        "WARNING": "orange"}
    _HEADERS: List[str] = ["Время", "Статус", "Информация"]

    def __init__(self) -> None:
        super().__init__()
        self._dir_name: str = ut.get_dir_name()
        self._init_ui()

    def _get_logs(self) -> str:
        """
        Method returns logs from table.
        :return: logs.
        """

        logs = ""
        for row in range(self.rowCount()):
            log_time = self.cellWidget(row, 0).text()
            level = self.cellWidget(row, 1).text()
            message = self.cellWidget(row, 2).text()
            logs += f"[{log_time} {level}] {message}\n"
        return logs

    def _init_ui(self) -> None:
        """
        Method creates table.
        """

        self.setColumnCount(len(self._HEADERS))
        self.setHorizontalHeaderLabels(self._HEADERS)
        for column in range(len(self._HEADERS)):
            mode = QHeaderView.Stretch if column == 2 else QHeaderView.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(column, mode)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().hide()
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_context_menu)

    @pyqtSlot(str, str, str)
    def add_log(self, log_time: str, level: str, message: str) -> None:
        """
        Slot adds a new entry to the table.
        :param log_time: log time;
        :param level: log level;
        :param message: log message.
        """

        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        for column, text in enumerate((log_time, level, message)):
            label = QLabel(text)
            if column == 1:
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet(f"color: {self._COLORS_FOR_LOGS.get(level, 'UNKNOWN')}")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.setCellWidget(row_count, column, label)
        self.scrollToBottom()
        for column in range(len(self._HEADERS)):
            mode = QHeaderView.Stretch if column == 2 else QHeaderView.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(column, mode)

    @pyqtSlot()
    def clear_logs(self) -> None:
        """
        Slot to clear logs in table.
        """

        while self.rowCount() > 0:
            self.removeRow(self.rowCount() - 1)

    @pyqtSlot()
    def copy_logs(self) -> None:
        """
        Slot to copy all logs.
        """

        QCoreApplication.instance().clipboard().setText(self._get_logs())

    @pyqtSlot()
    def save_logs(self) -> None:
        """
        Slot to save all logs to file.
        """

        file_name = os.path.join(self._dir_name, "logs.txt")
        file_name = QFileDialog.getSaveFileName(self, "Сохранить в файл", file_name, filter="Text file (*.txt)")[0]
        if file_name:
            self._dir_name = os.path.dirname(file_name)
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(self._get_logs())

    @pyqtSlot(QPoint)
    def show_context_menu(self, position: QPoint) -> None:
        """
        Slot shows context menu for table.
        :param position: position to show context.
        """

        menu = QMenu(self)
        action_copy = QAction(QIcon(os.path.join(ut.DIR_MEDIA, "copy.png")), "Копировать")
        action_copy.triggered.connect(self.copy_logs)
        menu.addAction(action_copy)
        action_save = QAction(QIcon(os.path.join(ut.DIR_MEDIA, "save.png")), "Сохранить")
        action_save.triggered.connect(self.save_logs)
        menu.addAction(action_save)
        action_clear = QAction(QIcon(os.path.join(ut.DIR_MEDIA, "clear.png")), "Очистить")
        action_clear.triggered.connect(self.clear_logs)
        menu.addAction(action_clear)
        menu.exec_(self.horizontalHeader().mapToGlobal(position))
