import logging
import os
from functools import partial
from typing import Dict, Generator, List, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QPoint, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QComboBox, QHeaderView, QLabel, QMenu, QPushButton, QSizePolicy, QTableWidget,
                             QWidget)
from gui.filter_dialog_window import FilterDialog
from gui.filter_widget import FilterWidget
from gui.router_params_dialog_window import DialogMode
from gui.utils import DIR_MEDIA
from gui.vertical_label import VerticalLabel


class FilterTable(QTableWidget):
    """
    Class for table widget to display switch filters.
    """

    INITIAL_COLUMN_COUNT: int = 4
    INITIAL_ROW_COUNT: int = 2
    comment_should_be_added: pyqtSignal = pyqtSignal(str, str, str, str)
    dialog_window_should_be_displayed: pyqtSignal = pyqtSignal(DialogMode, str)
    filter_should_be_added: pyqtSignal = pyqtSignal(str, str, str, str)
    filter_should_be_changed: pyqtSignal = pyqtSignal(str, str, str, str)
    filter_should_be_deleted: pyqtSignal = pyqtSignal(str, str, str)
    router_should_be_deleted: pyqtSignal = pyqtSignal(str)
    table_should_be_updated: pyqtSignal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.button_update_table: QPushButton = QPushButton("Обновить таблицу")
        self.buttons_to_delete: List[QPushButton] = []
        self.buttons_to_distribute: List[QPushButton] = []
        self.combo_boxes_enable_filters: List[QComboBox] = []
        self._data: List[Tuple[str, Dict[Tuple[str, str], Dict[str, str]], bool]] = []
        self._mac_and_targets: Dict[Tuple[str, str], str] = {}
        self._init_ui()

    def _add_button_to_delete(self, row: int, column: int, mac_address: str, target: str) -> None:
        """
        Method creates button to delete filter with given MAC address and target
        to all routers.
        :param row: row in table for button;
        :param column: column in table for button;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        button: QPushButton = QPushButton("")
        button.setIcon(QIcon(os.path.join(DIR_MEDIA, "delete.png")))
        button.setToolTip(f"Удалить фильтр {mac_address} {target} из всех коммутаторов")
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        button.clicked.connect(self.delete_filter_from_all_routers)
        self.buttons_to_delete.append(button)
        self.setCellWidget(row, column, button)

    def _add_button_to_distribute(self, row: int, column: int, mac_address: str, target: str) -> QPushButton:
        """
        Method creates button to add filter with given MAC address and target
        from all routers.
        :param row: row in table for button;
        :param column: column in table for button;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        :return: button.
        """

        button: QPushButton = QPushButton("")
        button.setIcon(QIcon(os.path.join(DIR_MEDIA, "arrow.png")))
        button.setToolTip(f"Установить фильтр {mac_address} {target} на все коммутаторы")
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        button.clicked.connect(self.add_filter_to_all_routers)
        self.buttons_to_distribute.append(button)
        self.setCellWidget(row, column, button)
        return button

    def _add_filter_label(self, row: int, mac_address: str, target: str, comment: str) -> None:
        """
        Method creates label for filter with given MAC address and target.
        :param row: row in table for label;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        """

        label_filter: FilterWidget = FilterWidget(mac_address, target, comment)
        label_filter.setContextMenuPolicy(Qt.CustomContextMenu)
        label_filter.customContextMenuRequested.connect(partial(self.show_context_menu_for_filter, label_filter, row))
        self.setCellWidget(row, 0, label_filter)

    def _add_new_filter(self, row: int, mac_address: str, target: str, comment: str) -> None:
        """
        Method add new row with filter with given MAC address and target to table.
        :param row: row in table for filter;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        """

        self.insertRow(row)
        self._add_filter_label(row, mac_address, target, comment)
        for column, (_, statistics, bad_router) in enumerate(self._data, start=1):
            combo_box = self._create_combo_box(mac_address, target, statistics, bad_router)
            self.combo_boxes_enable_filters.append(combo_box)
            self.setCellWidget(row, column, combo_box)

    def _add_router(self, mac_and_targets: List[Tuple[str, str, str]], router_index: int, router_ip_address: str,
                    router_statistics: Dict[Tuple[str, str], Dict[str, str]], bad_router: bool) -> None:
        """
        Method adds new column with router statistics.
        :param mac_and_targets: list with MAC addresses, filter targets (SRC or DST)
        and comments in first column of table;
        :param router_index: index of router;
        :param router_ip_address: IP address of router;
        :param router_statistics: router filter statistics;
        :param bad_router: if True then failed to connect to router.
        """

        column = router_index + 1
        if router_index:
            self.insertColumn(column)
            self.setSpan(0, 1, 1, column)
        self._add_router_label(column, router_ip_address, bad_router)
        for row, (mac_address, target, _) in enumerate(mac_and_targets, start=2):
            combo_box = self._create_combo_box(mac_address, target, router_statistics, bad_router)
            self.combo_boxes_enable_filters.append(combo_box)
            self.setCellWidget(row, column, combo_box)

    def _add_router_label(self, column: int, router_ip_address: str, bad_router: bool) -> None:
        """
        Method adds label for router.
        :param column: column in table for router;
        :param router_ip_address: IP address of router;
        :param bad_router: if True then failed to connect to router.
        """

        label_router: VerticalLabel = VerticalLabel(router_ip_address)
        if bad_router:
            label_router.setStyleSheet("color: red;")
            label_router.setToolTip(f"При работе с коммутатором {router_ip_address} возникли ошибки")
        label_router.setFixedWidth(40)
        label_router.setAlignment(Qt.AlignCenter)
        label_router.setContextMenuPolicy(Qt.CustomContextMenu)
        label_router.customContextMenuRequested.connect(partial(self.show_context_menu_for_router, label_router,
                                                                column))
        self.setCellWidget(1, column, label_router)

    def _clear_content_in_table(self) -> None:
        """
        Method clears table and removes router filter statistics from table.
        """

        while self.columnCount() > self.INITIAL_COLUMN_COUNT:
            self.removeColumn(self.columnCount() - 3)
        while self.rowCount() > self.INITIAL_ROW_COUNT:
            self.removeRow(self.rowCount() - 1)
        self.removeCellWidget(1, 1)

    def _create_combo_box(self, mac_address: str, target: str, statistics: Dict[Tuple[str, str], Dict[str, str]],
                          bad_router: bool) -> QComboBox:
        """
        Method creates combo box widget to enable/disable filter in router.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param statistics: router statistics;
        :param bad_router: if True then failed to connect to router.
        :return: combo box widget.
        """

        def get_current_text(disabled: Optional[str]) -> str:
            return {"true": "Выкл",
                    "false": "Вкл"}.get(disabled, "-")

        combo_box: QComboBox = QComboBox()
        combo_box.setEditable(True)
        combo_box.lineEdit().setReadOnly(True)
        combo_box.lineEdit().setAlignment(Qt.AlignCenter)
        combo_box.addItems(["Вкл", "Выкл", "-"])
        combo_box.setCurrentText(get_current_text(statistics[(mac_address, target)].get("disabled", "")))
        combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        combo_box.currentTextChanged.connect(self.enable_filter)
        combo_box.setDisabled(bad_router)
        return combo_box

    def _fill_column_with_delete_buttons(self, mac_and_targets: List[Tuple[str, str, str]], column: int) -> None:
        """
        Method creates buttons to delete filter from all routers in table.
        :param mac_and_targets: list with MAC addresses and filter targets (SRC or DST)
        and comments in first column of table;
        :param column: column to place buttons.
        """

        for row, (mac_address, target, _) in enumerate(mac_and_targets, start=2):
            self._add_button_to_delete(row, column, mac_address, target)

    def _fill_column_with_distribute_buttons(self, mac_and_targets: List[Tuple[str, str, str]], column: int) -> None:
        """
        Method creates buttons to add filter to all routers in table.
        :param mac_and_targets: list with MAC addresses and filter targets (SRC or DST)
        and comments in first column of table;
        :param column: column to place buttons.
        """

        for row, (mac_address, target, _) in enumerate(mac_and_targets, start=2):
            self._add_button_to_distribute(row, column, mac_address, target)

    def _fill_column_with_filters(self, mac_and_targets: List[Tuple[str, str, str]]) -> None:
        """
        Method fills first column with filters.
        :param mac_and_targets: list with MAC addresses, filter targets (SRC or DST)
        and comments in first column of table.
        """

        self.setRowCount(len(mac_and_targets) + self.INITIAL_ROW_COUNT)
        for row, (mac_address, target, comment) in enumerate(mac_and_targets, start=2):
            self._add_filter_label(row, mac_address, target, comment)

    def _get_row_and_column(self, widget: QWidget) -> Optional[Tuple[int, int]]:
        """
        Method returns row and column of cell in table where given widget is located.
        :param widget: widget.
        :return: row and column.
        """

        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                if widget is self.cellWidget(row, column):
                    return row, column
        return None

    def _get_routers_with_filter(self, mac_address: str, target: str) -> Generator:
        """
        Method returns IP addresses of routers that have given filter.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        :return: IP addresses of routers.
        """

        for router_ip_address, statistics, bad_router in self._data:
            if bad_router:
                continue
            if statistics.get((mac_address, target), None):
                yield router_ip_address

    def _get_routers_without_filter(self, mac_address: str, target: str) -> Generator:
        """
        Method returns IP addresses of routers that have not given filter.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        :return: column for router in table and IP addresses of routers.
        """

        for column, (router_ip_address, statistics, bad_router) in enumerate(self._data, start=1):
            if bad_router:
                continue
            if not statistics.get((mac_address, target), None):
                yield column, router_ip_address

    def _init_ui(self) -> None:
        """
        Method creates main widgets on table.
        """

        self.setColumnCount(self.INITIAL_COLUMN_COUNT)
        self.horizontalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.setRowCount(self.INITIAL_ROW_COUNT)
        self.setCellWidget(0, 0, self.button_update_table)
        self.button_update_table.clicked.connect(self.send_signal_to_update_table)
        self._set_routers_label()

        label_mac_addresses = QLabel("MAC адреса")
        label_mac_addresses.setAlignment(Qt.AlignBottom)
        self.setCellWidget(1, 0, label_mac_addresses)
        self.setCellWidget(1, 2, VerticalLabel("Удалить"))
        self.setCellWidget(1, 3, VerticalLabel("Распространить"))

    def _send_signals_to_change_filter_comment(self, mac_address: str, target: str, comment: str) -> None:
        """
        Method sends signals to all routers to change comment on given filter.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        """

        for router_ip_address, router_statistics, bad_router in self._data:
            if bad_router:
                continue
            if router_statistics.get((mac_address, target), {}):
                self.comment_should_be_added.emit(router_ip_address, mac_address, target, comment)

    def _set_column_size_policy(self) -> None:
        column_number = self.INITIAL_COLUMN_COUNT + len(self._data) - 1
        for column in range(column_number):
            self.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)

    def _set_routers_label(self) -> None:
        label_routers = QLabel("Коммутаторы")
        label_routers.setAlignment(Qt.AlignCenter)
        self.setCellWidget(0, 1, label_routers)

    def _update_data(self, new_router_ip_address: str, new_router_statistics: Dict[Tuple[str, str], Dict[str, str]],
                     bad_router: bool) -> List[Tuple[str, str, str]]:
        """
        Method updates data with router statistics.
        :param new_router_ip_address: IP address of new router;
        :param new_router_statistics: statistics of new router;
        :param bad_router: if True then failed to connect to new router.
        :return: list with MAC addresses and targets of all filters.
        """

        for mac_and_target, data in new_router_statistics.items():
            if data.get("comment", None) and not self._mac_and_targets.get(mac_and_target, None):
                self._mac_and_targets[mac_and_target] = data["comment"]
            elif mac_and_target not in self._mac_and_targets:
                self._mac_and_targets[mac_and_target] = ""
        mac_and_targets = sorted([(*mac_and_target, comment) for mac_and_target, comment in
                                  self._mac_and_targets.items()], key=lambda x: (x[0], x[1]))
        self._data.append((new_router_ip_address, new_router_statistics, bad_router))
        for _, router_statistics, _ in self._data:
            for mac_and_target in self._mac_and_targets:
                if mac_and_target not in router_statistics:
                    router_statistics[mac_and_target] = {}
        return mac_and_targets

    def _update_table(self, mac_and_targets: List[Tuple[str, str, str]]) -> None:
        """
        Method updates table.
        :param mac_and_targets: list with MAC addresses, targets and comments of all filters.
        """

        self._fill_column_with_filters(mac_and_targets)
        for router_index, (router_ip_address, router_statistics, bad_router) in enumerate(self._data):
            self._add_router(mac_and_targets, router_index, router_ip_address, router_statistics, bad_router)
        self._fill_column_with_delete_buttons(mac_and_targets, len(self._data) + 1)
        self._fill_column_with_distribute_buttons(mac_and_targets, len(self._data) + 2)
        self._set_column_size_policy()

    @pyqtSlot()
    def add_filter_to_all_routers(self) -> None:
        """
        Slot sends signal to add given filter to all routers.
        """

        row_and_column = self._get_row_and_column(self.sender())
        if row_and_column:
            row = row_and_column[0]
            mac_address, target, comment = self.cellWidget(row, 0).get_data()
            for column, router_ip_address in self._get_routers_without_filter(mac_address, target):
                combo_box = self.cellWidget(row, column)
                combo_box.setCurrentText("Вкл")
                self.filter_should_be_added.emit(router_ip_address, mac_address, target, comment)

    @pyqtSlot(str, str)
    def add_filter_to_table(self, mac_address: str, target: str) -> None:
        """
        Slot adds new filter with given MAC address and target to filters.
        :param mac_address: MAC address of new filter;
        :param target: target (SRC or DST) of new filter.
        """

        if (mac_address, target) in self._mac_and_targets:
            logging.warning("Filter %s %s already exists", mac_address, target)
            return
        if not self._data:
            return
        comment = ""
        self._mac_and_targets[(mac_address, target)] = comment
        for _, statistics, _ in self._data:
            statistics[(mac_address, target)] = {}
        mac_and_targets = sorted([(*mac_and_target, comment) for mac_and_target, comment in
                                  self._mac_and_targets.items()], key=lambda x: (x[0], x[1]))
        row = mac_and_targets.index((mac_address, target, comment)) + 2
        self._add_new_filter(row, mac_address, target, comment)
        self._add_button_to_delete(row, len(self._data) + 1, mac_address, target)
        button = self._add_button_to_distribute(row, len(self._data) + 2, mac_address, target)
        button.click()

    @pyqtSlot(str, dict, bool)
    def add_statistics(self, new_router_ip_address: str, new_router_statistics: Dict[Tuple[str, str], Dict[str, str]],
                       bad_router: bool) -> None:
        """
        Slot to add new statistics for router on table.
        :param new_router_ip_address: IP address of new router;
        :param new_router_statistics: filter statistics of new router;
        :param bad_router: if True then failed to connect to router.
        """

        mac_and_filters = self._update_data(new_router_ip_address, new_router_statistics, bad_router)
        self._clear_content_in_table()
        self._update_table(mac_and_filters)

    @pyqtSlot()
    def delete_filter_from_all_routers(self) -> None:
        """
        Slot sends signal to delete given filter from all routers.
        """

        row_and_column = self._get_row_and_column(self.sender())
        if row_and_column:
            row = row_and_column[0]
            mac_address, target = self.cellWidget(row, 0).get_mac_address_and_target()
            for router_ip_address in self._get_routers_with_filter(mac_address, target):
                self.filter_should_be_deleted.emit(router_ip_address, mac_address, target)
            self.removeRow(row)
            self._mac_and_targets.pop((mac_address, target))
            for _, statistics, _ in self._data:
                statistics.pop((mac_address, target))

    @pyqtSlot(int, str)
    def delete_router(self, column: int, router_ip_address: str) -> None:
        """
        Slot deletes router from table.
        :param column: column of router in table;
        :param router_ip_address: IP address of router.
        """

        if len(self._data) > 1:
            self.removeColumn(column)
            if not self.cellWidget(0, 1) or not self.cellWidget(0, 1).text():
                self._set_routers_label()
        else:
            self._clear_content_in_table()
        router_index = None
        for index, (ip_address, _, _) in enumerate(self._data):
            if ip_address == router_ip_address:
                router_index = index
                break
        if router_index is not None:
            self._data.pop(router_index)
        self._set_column_size_policy()
        self.router_should_be_deleted.emit(router_ip_address)

    @pyqtSlot(str)
    def enable_filter(self, current_text: str) -> None:
        """
        Slot sends signal to enable or disable filter.
        :param current_text: current text in combo box.
        """

        row_and_column = self._get_row_and_column(self.sender())
        if row_and_column:
            row, column = row_and_column
            state = {"Вкл": "enable",
                     "Выкл": "disable",
                     "-": ""}.get(current_text)
            router_ip_address = self.cellWidget(1, column).text()
            mac_address, target = self.cellWidget(row, 0).get_mac_address_and_target()
            self.filter_should_be_changed.emit(router_ip_address, mac_address, target, state)

    @pyqtSlot()
    def send_signal_to_update_table(self) -> None:
        """
        Slot sends signal to update table.
        """

        self.buttons_to_delete.clear()
        self.buttons_to_distribute.clear()
        self.combo_boxes_enable_filters.clear()
        self._data.clear()
        self._mac_and_targets.clear()
        self.table_should_be_updated.emit()

    @pyqtSlot(FilterWidget, int, QPoint)
    def show_context_menu_for_filter(self, filter_widget: FilterWidget, row: int, position: QPoint) -> None:
        """
        Slot shows context menu for filter.
        :param filter_widget: widget for filter;
        :param row: row for label in table;
        :param position: position for menu.
        """

        filter_name = filter_widget.get_filter_name()
        action_delete: QAction = QAction(QIcon(os.path.join(DIR_MEDIA, "delete.png")),
                                         f"Удалить фильтр {filter_name} из всех коммутаторов")
        button_to_delete = self.cellWidget(row, len(self._data) + 1)
        action_delete.triggered.connect(button_to_delete.click)
        action_distribute: QAction = QAction(QIcon(os.path.join(DIR_MEDIA, "arrow.png")),
                                             f"Добавить фильтр {filter_name} во все коммутаторы")
        button_to_distribute = self.cellWidget(row, len(self._data) + 2)
        action_distribute.triggered.connect(button_to_distribute.click)
        action_change_comment: QAction = QAction(QIcon(os.path.join(DIR_MEDIA, "change.png")),
                                                 f"Изменить комментарий для фильтра {filter_name}")
        action_change_comment.triggered.connect(lambda: self.show_dialog_window_for_filter(filter_widget))
        menu: QMenu = QMenu(self)
        menu.addAction(action_delete)
        menu.addAction(action_distribute)
        menu.addAction(action_change_comment)
        menu.exec_(filter_widget.mapToGlobal(position))

    @pyqtSlot(QLabel, int, QPoint)
    def show_context_menu_for_router(self, label: QLabel, column: int, position: QPoint) -> None:
        """
        Slot shows context menu for router.
        :param label: label of router;
        :param column: column of router in table;
        :param position: position for menu.
        """

        router_ip_address = label.text()
        action_add_params: QAction = QAction(QIcon(os.path.join(DIR_MEDIA, "settings.png")),
                                             f"Задать параметры подключения к коммутатору {router_ip_address}")
        action_add_params.triggered.connect(lambda: self.dialog_window_should_be_displayed.emit(DialogMode.SINGLE,
                                                                                                router_ip_address))
        action_delete: QAction = QAction(QIcon(os.path.join(DIR_MEDIA, "delete.png")),
                                         f"Удалить коммутатор {router_ip_address}")
        action_delete.triggered.connect(lambda: self.delete_router(column, router_ip_address))
        menu: QMenu = QMenu()
        menu.addAction(action_add_params)
        menu.addAction(action_delete)
        menu.exec_(label.mapToGlobal(position))

    @pyqtSlot(FilterWidget)
    def show_dialog_window_for_filter(self, filter_widget: FilterWidget) -> None:
        """
        Slot shows dialog window to change filter comment.
        :param filter_widget: widget for filter.
        """

        dialog_window = FilterDialog(filter_widget.comment)
        if dialog_window.exec_():
            comment = dialog_window.get_comment()
            self._send_signals_to_change_filter_comment(filter_widget.mac_address, filter_widget.target, comment)
            filter_widget.set_comment(comment)
