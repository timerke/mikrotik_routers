import ast
import ipaddress
import logging
import os
from configparser import ConfigParser
from typing import Dict, List, Union
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from mikrotik.mikrotik import MikroTikRouter


class ConfigData(QObject):
    """
    Class to save data from config file.
    """

    CONFIG_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.ini")
    DEFAULT_CONFIG_DATA: Dict[str, str] = {"user": "admin",
                                           "password": "12345",
                                           "ip_addresses": "[]"}
    router_ip_address_added: pyqtSignal = pyqtSignal()
    statistics_finished: pyqtSignal = pyqtSignal()
    statistics_received: pyqtSignal = pyqtSignal(str, dict, bool)

    def __init__(self) -> None:
        super().__init__()
        data = self._read_config_file()
        self._ip_addresses: List[ipaddress.IPv4Address] = self._get_correct_ip_addresses(data["ip_addresses"])
        self._password: str = data["password"]
        self._user: str = data["user"]

    @staticmethod
    def _get_correct_ip_addresses(ip_addresses: List[str]) -> List[str]:
        """
        Method checks IP addresses and returns correct addresses.
        :param ip_addresses: list with IP addresses.
        :return: correct IP addresses.
        """

        init_len = len(ip_addresses)
        correct_ip_addresses = []
        for ip_address in ip_addresses:
            try:
                ip = ipaddress.ip_address(ip_address)
            except ValueError:
                continue
            correct_ip_addresses.append(ip)
        ip_addresses = list(set(correct_ip_addresses))
        if len(ip_addresses) != init_len:
            logging.warning("Config file contained incorrect IP addresses")
        return sorted(ip_addresses)

    def _read_config_file(self) -> Dict[str, Union[str, List[str]]]:
        """
        Method reads config file.
        :return: dictionary with data about login, password and IP addresses of routers.
        """

        config_parser = ConfigParser()
        config_parser.read(self.CONFIG_PATH)
        bad_config = False
        if not config_parser.has_section("MAIN"):
            logging.warning("Could not read config file")
            bad_config = True
            config_parser.add_section("MAIN")
        data = {}
        for subsection in ("user", "password", "ip_addresses"):
            if subsection not in config_parser["MAIN"] and not bad_config:
                logging.warning("Failed to read subsection '%s' from config file", subsection)
            value = config_parser.get("MAIN", subsection, fallback=self.DEFAULT_CONFIG_DATA[subsection])
            data[subsection] = ast.literal_eval(value) if subsection == "ip_addresses" else value
        return data

    def _save_to_config_file(self, config_data: Dict[str, Union[str, List[str]]]) -> None:
        """
        Method saves data about login, password and IP addresses of routers to config file.
        :param config_data: data to save.
        """

        config_parser = ConfigParser()
        config_parser.add_section("MAIN")
        for key, value in config_data.items():
            if value is not None:
                config_parser.set("MAIN", key, str(value))
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as file:
            config_parser.write(file)

    @pyqtSlot(str, str, str)
    def add_filter_to_router(self, router_ip_address: str, mac_address: str, target: str) -> None:
        """
        Slot adds given filter to given router.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        try:
            router = MikroTikRouter(router_ip_address, self._user, self._password)
            router.add_filter(mac_address, target)
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
        if ip_address in self._ip_addresses:
            logging.warning("Router with IP address %s already exists", str(ip_address))
            return
        self._ip_addresses.append(ip_address)
        self._ip_addresses = sorted(self._ip_addresses)
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
            router = MikroTikRouter(router_ip_address, self._user, self._password)
            router.enable_filter(mac_address, target, state)
            router.close()
            logging.info("Filter %s %s state on the router %s was changed", mac_address, target, router_ip_address)
        except Exception:
            logging.error("Failed to change filter %s %s state on the router %s", mac_address, target,
                          router_ip_address)

    @pyqtSlot(str, str, str)
    def delete_filter_from_router(self, router_ip_address: str, mac_address: str, target: str) -> None:
        """
        Slot deletes given filter from given router.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        try:
            router = MikroTikRouter(router_ip_address, self._user, self._password)
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
            self._ip_addresses.remove(ip_address)
            logging.info("Router %s was deleted", router_ip_address)
        except Exception:
            logging.error("Failed to delete router %s", router_ip_address)

    @pyqtSlot()
    def get_statistics(self) -> None:
        """
        Slot receives filter statistics from all known routers.
        """

        for ip_address in self._ip_addresses:
            str_ip_address = str(ip_address)
            statistics = {}
            bad_router = False
            try:
                router = MikroTikRouter(str_ip_address, self._user, self._password)
            except Exception:
                bad_router = True
                logging.error("Failed to connect to router %s", str_ip_address)
            try:
                statistics = router.get_statistics()
            except Exception:
                bad_router = True
                logging.error("Failed to receive filter statistics from router %s", str_ip_address)
            else:
                router.close()
            self.statistics_received.emit(str_ip_address, statistics, bad_router)
        self.statistics_finished.emit()

    def save(self) -> None:
        """
        Method saves config data to config file.
        """

        data = {"user": self._user,
                "password": self._password,
                "ip_addresses": [str(ip_address) for ip_address in self._ip_addresses]}
        self._save_to_config_file(data)
