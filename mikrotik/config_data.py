import ipaddress
import logging
import os
from configparser import ConfigParser
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from gui.utils import get_dir_name
from mikrotik.mikrotik import MikroTikRouter


class ConfigData(QObject):
    """
    Class to save data from config file.
    """

    CONFIG_PATH: str = os.path.join(get_dir_name(), "config.ini")
    DEFAULT_CONFIG_DATA: Dict[str, str] = {"user": "admin",
                                           "password": "12345"}
    data_for_dialog_window_send: pyqtSignal = pyqtSignal(dict, list)
    router_ip_address_added: pyqtSignal = pyqtSignal()
    statistics_finished: pyqtSignal = pyqtSignal()
    statistics_received: pyqtSignal = pyqtSignal(str, dict, bool)

    def __init__(self) -> None:
        super().__init__()
        self._default_data: Dict[str, str] = {}
        self._routers: List[Dict[str, str]] = self._read_config_file()

    def _get_user_and_password_for_router(self, router_ip_address: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Method returns user name and password for router with given IP address.
        :param router_ip_address: IP address of router.
        :return: user name and password for router.
        """

        try:
            ip_address = ipaddress.ip_address(router_ip_address)
            for router in self._routers:
                if ip_address == router.get("ip_address", None):
                    return (router["user"] if router["user"] is not None else self._default_data["user"],
                            router["password"] if router["password"] is not None else self._default_data["password"])
        except Exception:
            pass
        logging.error("Failed to get user name and password for router %s", router_ip_address)
        raise ValueError

    def _is_there_already_router(self, ip_address: ipaddress.IPv4Address) -> bool:
        """
        Method check if there is already given IP address.
        :param ip_address: IP address of router.
        :return: True if given IP address already exists.
        """

        for router in self._routers:
            if ip_address == router.get("ip_address", None):
                return True
        return False

    def _read_config_file(self) -> List[Dict[str, str]]:
        """
        Method reads config file.
        :return: list with data about routers.
        """

        config_parser = ConfigParser()
        config_parser.read(self.CONFIG_PATH)
        self._read_default_user_and_password(config_parser)
        return self._read_routers_from_config(config_parser)

    def _read_default_user_and_password(self, config_parser: ConfigParser) -> None:
        """
        Method reads default user name and password for routers.
        :param config_parser: config parser.
        """

        if not config_parser.has_section("MAIN"):
            logging.warning("There are no default user name and password in config file")
            config_parser.add_section("MAIN")
        self._default_data = {}
        for subsection in ("user", "password"):
            self._default_data[subsection] = config_parser.get("MAIN", subsection,
                                                               fallback=self.DEFAULT_CONFIG_DATA[subsection])

    @staticmethod
    def _read_routers_from_config(config_parser: ConfigParser) -> List[Dict[str, str]]:
        """
        Method reads router parameters from config file.
        :param config_parser: config parser.
        :return: list with data about routers.
        """

        data = []
        for section in config_parser.sections():
            try:
                ip_address = ipaddress.ip_address(section)
            except Exception:
                continue
            router_data = {"ip_address": ip_address,
                           "user": config_parser.get(section, "user", fallback=None),
                           "password": config_parser.get(section, "password", fallback=None)}
            data.append(router_data)
        return sorted(data, key=lambda x: x["ip_address"])

    def _save_default_to_config_file(self, config_parser: ConfigParser) -> None:
        """
        Method saves default data (user name and password) to config file.
        :param config_parser: config parser.
        """

        config_parser.add_section("MAIN")
        for key, value in self._default_data.items():
            config_parser.set("MAIN", key, value)

    def _save_routers_to_config_file(self, config_parser: ConfigParser) -> None:
        """
        Method saves data about routers to config file.
        :param config_parser: config parser.
        """

        for router_data in self._routers:
            section = str(router_data["ip_address"])
            config_parser.add_section(section)
            if router_data.get("user", None) is not None:
                config_parser.set(section, "user", router_data["user"])
            if router_data.get("password", None) is not None:
                config_parser.set(section, "password", router_data["password"])

    @pyqtSlot(str, str, str)
    def add_filter_to_router(self, router_ip_address: str, mac_address: str, target: str) -> None:
        """
        Slot adds given filter to given router.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        try:
            user, password = self._get_user_and_password_for_router(router_ip_address)
            router = MikroTikRouter(router_ip_address, user, password)
            router.add_filter(mac_address, target)
            filter_index = router.get_indices_of_filter(mac_address, target)[-1]
            drop_indices = router.get_indices_of_drop_filters()
            if drop_indices:
                router.move_filter(filter_index, drop_indices[0])
            router.close()
            logging.info("Filter %s %s was added to router %s", mac_address, target, router_ip_address)
        except Exception:
            logging.error("Failed to add filter %s %s to router %s", mac_address, target, router_ip_address)

    @pyqtSlot(str)
    def add_ip_address(self, ip_address: str) -> None:
        """
        Slot adds new router IP address.
        :param ip_address: IP address of new router.
        """

        try:
            ip_address = ipaddress.ip_address(ip_address)
        except ValueError:
            logging.warning("Incorrect IP address: %s", str(ip_address))
            return
        if self._is_there_already_router(ip_address):
            logging.warning("Router with IP address %s already exists", str(ip_address))
            return
        self._routers.append({"ip_address": ip_address,
                              "user": None,
                              "password": None})
        self._routers = sorted(self._routers, key=lambda x: x["ip_address"])
        self.router_ip_address_added.emit()
        logging.info("Added IP address %s", str(ip_address))

    @pyqtSlot(str, str, str, str)
    def change_filter_state(self, router_ip_address: str, mac_address: str, target: str, state: str) -> None:
        """
        Slot changes filter state on router with given IP address.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address;
        :param target: target;
        :param state: new state of filter.
        """

        try:
            user, password = self._get_user_and_password_for_router(router_ip_address)
            router = MikroTikRouter(router_ip_address, user, password)
            router.enable_filter(mac_address, target, state)
            router.close()
            logging.info("Filter %s %s state on the router %s was changed", mac_address, target, router_ip_address)
        except Exception:
            logging.error("Failed to change filter %s %s state on the router %s", mac_address, target,
                          router_ip_address)

    @pyqtSlot()
    def collect_data_for_dialog_window(self):
        """
        Slot sends data for dialog window to change router parameters.
        """

        self.data_for_dialog_window_send.emit(self._default_data, self._routers)

    @pyqtSlot(str, str, str)
    def delete_filter_from_router(self, router_ip_address: str, mac_address: str, target: str) -> None:
        """
        Slot deletes given filter from given router.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        try:
            user, password = self._get_user_and_password_for_router(router_ip_address)
            router = MikroTikRouter(router_ip_address, user, password)
            if not router.delete_filter(mac_address, target):
                logging.error("Failed to delete filter %s %s from router %s: filter not found", mac_address, target,
                              router_ip_address)
            else:
                logging.info("Filter %s %s was deleted from router %s", mac_address, target, router_ip_address)
            router.close()
        except Exception:
            logging.error("Failed to delete filter %s %s from router %s", mac_address, target, router_ip_address)

    @pyqtSlot(str)
    def delete_router(self, router_ip_address: str) -> None:
        """
        Slot deletes router IP address.
        :param router_ip_address: IP address of router.
        """

        try:
            ip_address = ipaddress.ip_address(router_ip_address)
            router_index = None
            for index, router in enumerate(self._routers):
                if router.get("ip_address") == ip_address:
                    router_index = index
            if router_index is not None:
                self._routers.pop(router_index)
            logging.info("Router %s was deleted", router_ip_address)
        except Exception:
            logging.error("Failed to delete router %s", router_ip_address)

    @pyqtSlot()
    def get_statistics(self) -> None:
        """
        Slot receives filter statistics from all known routers.
        """

        for router in self._routers:
            router_ip_address = str(router.get("ip_address", None))
            statistics = {}
            bad_router = False
            try:
                user, password = self._get_user_and_password_for_router(router_ip_address)
                router = MikroTikRouter(router_ip_address, user, password)
            except Exception:
                bad_router = True
                logging.error("Failed to connect to router %s", router_ip_address)
            try:
                statistics = router.get_statistics()
            except Exception:
                bad_router = True
                logging.error("Failed to receive filter statistics from router %s", router_ip_address)
            else:
                router.close()
            self.statistics_received.emit(router_ip_address, statistics, bad_router)
        self.statistics_finished.emit()

    def save(self) -> None:
        """
        Method saves config data to config file.
        """

        config_parser = ConfigParser()
        self._save_default_to_config_file(config_parser)
        self._save_routers_to_config_file(config_parser)
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as file:
            config_parser.write(file)

    @pyqtSlot(dict, list)
    def set_new_default_data_and_routers(self, new_default_data: Dict[str, str],
                                         new_routers_data: List[Dict[str, str]]) -> None:
        """
        Slot sets new default user name and password and new routers data.
        :param new_default_data: dictionary with new default user name and password;
        :param new_routers_data: list with new routers data.
        """

        self._default_data = new_default_data
        self._routers = new_routers_data
        logging.info("New parameters were set for routers")
