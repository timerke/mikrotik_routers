import ipaddress
import logging
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from mikrotik.config_data import read_config_file, save_config_file
from mikrotik.mikrotik import MikroTikRouter


class Routers(QThread):
    """
    Class to work with MikroTik routers.
    """

    data_for_dialog_window_send: pyqtSignal = pyqtSignal(dict, list)
    filter_added: pyqtSignal = pyqtSignal(str, str, str, str, str)
    router_ip_address_added: pyqtSignal = pyqtSignal()
    statistics_finished: pyqtSignal = pyqtSignal()
    statistics_received: pyqtSignal = pyqtSignal(str, dict, bool)

    def __init__(self) -> None:
        super().__init__()
        self._default_data: Dict[str, str] = {}
        self._routers: List[Dict[str, str]] = []

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

    @pyqtSlot(str, str, str, str)
    def add_comment_to_filter(self, router_ip_address: str, mac_address: str, target: str, comment: str) -> None:
        """
        Slot adds comment to given filter on given router.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment to add.
        """

        try:
            user, password = self._get_user_and_password_for_router(router_ip_address)
            router = MikroTikRouter(router_ip_address, user, password)
            router.add_comment(mac_address, target, comment)
            logging.info("Comment '%s' was added to filter %s %s on the router %s", comment, mac_address, target,
                         router_ip_address)
        except Exception:
            logging.error("Comment '%s' could not be added to the filter %s %s on the router %s", comment, mac_address,
                          target, router_ip_address)

    @pyqtSlot(str, str, str, str)
    def add_filter_to_router(self, router_ip_address: str, mac_address: str, target: str, comment: str) -> None:
        """
        Slot adds given filter to given router.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        """

        try:
            user, password = self._get_user_and_password_for_router(router_ip_address)
            router = MikroTikRouter(router_ip_address, user, password)
            router.add_filter(mac_address, target, comment)
            filter_index = router.get_indices_of_filter(mac_address, target)[-1]
            drop_indices = router.get_indices_of_drop_filters()
            if drop_indices:
                router.move_filter(filter_index, drop_indices[0])
            disabled = "false"
            logging.info("Filter %s %s was added to router %s", mac_address, target, router_ip_address)
        except Exception:
            disabled = "-"
            logging.error("Failed to add filter %s %s to router %s", mac_address, target, router_ip_address)
        finally:
            self.filter_added.emit(router_ip_address, mac_address, target, comment, disabled)
            if router is not None:
                router.close()

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
        self.save_config_file()

    @pyqtSlot(str, str, str, str, str)
    def change_filter_state(self, router_ip_address: str, mac_address: str, target: str, comment: str, state: str
                            ) -> None:
        """
        Slot changes filter state on router with given IP address.
        :param router_ip_address: router IP address;
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment fot filter;
        :param state: new state of filter.
        """

        try:
            user, password = self._get_user_and_password_for_router(router_ip_address)
            router = MikroTikRouter(router_ip_address, user, password)
            if not router.enable_filter(mac_address, target, state):
                state = {"enable": "false",
                         "disable": "true"}.get(state, "")
                router.add_filter(mac_address, target, comment, state)
            logging.info("Filter %s %s state on the router %s was changed", mac_address, target, router_ip_address)
        except Exception:
            if router:
                statistics = router.get_statistics()
                disabled = statistics.get((mac_address, target), {}).get("disabled", "-")
            else:
                disabled = "-"
            self.filter_added.emit(router_ip_address, mac_address, target, comment, disabled)
            logging.error("Failed to change filter %s %s state on the router %s", mac_address, target,
                          router_ip_address)
        finally:
            if router is not None:
                router.close()

    @pyqtSlot()
    def collect_data_for_dialog_window(self) -> None:
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
        except Exception:
            logging.error("Failed to delete filter %s %s from router %s", mac_address, target, router_ip_address)
        finally:
            if router is not None:
                router.close()

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
        else:
            self.save_config_file()

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
            if not bad_router:
                try:
                    statistics = router.get_statistics()
                except Exception:
                    bad_router = True
                    logging.error("Failed to receive filter statistics from router %s", router_ip_address)
                finally:
                    router.close()
            self.statistics_received.emit(router_ip_address, statistics, bad_router)
        self.statistics_finished.emit()

    @pyqtSlot()
    def read_config_file(self) -> None:
        self._default_data, self._routers = read_config_file()
        self.get_statistics()

    @pyqtSlot()
    def save_config_file(self) -> None:
        save_config_file(self._default_data, self._routers)

    @pyqtSlot(dict, list)
    def set_new_default_data_and_routers(self, new_default_data: Dict[str, str],
                                         new_routers_data: List[Dict[str, str]]) -> None:
        """
        Slot sets new default username and password and new routers data.
        :param new_default_data: dictionary with new default username and password;
        :param new_routers_data: list with new routers data.
        """

        self._default_data = new_default_data
        self._routers = new_routers_data
        logging.info("New parameters were set for routers")
        self.save_config_file()
