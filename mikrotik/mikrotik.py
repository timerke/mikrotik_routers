import logging
from typing import Dict, List, Optional, Tuple
import ros_api


class MikroTikRouter:
    """
    Class to work with MikroTik routers.
    """

    def __init__(self, ip_address: str, user: str, password: str) -> None:
        self._ip_address: str = ip_address
        self._password: str = password
        self._user: str = user
        self._router: ros_api.Api = ros_api.Api(self._ip_address, user=self._user, password=self._password)

    def _get_total_statistics(self) -> List[Tuple[str, str, Optional[str]]]:
        """
        Method gets filter statistics from router.
        :return: list with MAC address of filter, target of filter and state of filter.
        """

        result = self._router.talk("/interface/bridge/filter/print")
        statistics = []
        for item in result:
            mac = ""
            target = ""
            disabled = item.get("disabled", "")
            src_mac = item.get("src-mac-address", None)
            dst_mac = item.get("dst-mac-address", None)
            if src_mac is not None:
                mac = src_mac.split("/")[0]
                target = "SRC"
            if dst_mac is not None:
                mac = dst_mac.split("/")[0]
                target = "DST"
            statistics.append((mac.upper(), target.upper(), disabled))
        return statistics

    def add_filter(self, mac_address: str, target: str) -> None:
        """
        Method adds new filter to router.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        self._router.talk(f"/interface/bridge/filter/add\n=action=accept\n=chain=forward"
                          f"\n={target.lower()}-mac-address={mac_address}/FF:FF:FF:FF:FF:FF")

    def close(self) -> None:
        """
        Method closes connection to filter.
        """

        self._router.close()

    def delete_filter(self, mac_address: str, target: str) -> bool:
        """
        Method deletes filter from router.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        statistics = self._get_total_statistics()
        statistics.reverse()
        filter_was_deleted = False
        for index, (mac_item, target_item, _) in enumerate(statistics):
            if mac_item == mac_address and target_item == target:
                self._router.talk(f"/interface/bridge/filter/remove\n=numbers={len(statistics) - index - 1}")
                filter_was_deleted = True
        return filter_was_deleted

    def enable_filter(self, mac_address: str, target: str, state: str) -> None:
        """
        Method enables or disables some filter on router.
        :param mac_address: MAC address;
        :param target: src or dst;
        :param state: enable or disable.
        """

        for index, (mac_item, target_item, _) in enumerate(self._get_total_statistics()):
            if mac_item == mac_address and target_item == target:
                self._router.talk(f"/interface/bridge/filter/{state}\n=numbers={index}")
                break

    def get_statistics(self) -> Dict[Tuple[str, str], Optional[str]]:
        """
        Method receives filter statistics from router.
        :return: list with filter statistics.
        """

        statistics = {}
        multiple_filters = set()
        for mac, target, disabled in self._get_total_statistics():
            if not target:
                continue
            if (mac, target) not in statistics:
                statistics[(mac, target)] = disabled
            else:
                multiple_filters.add((mac, target))
        for mac, target in multiple_filters:
            logging.warning("There are several filters %s %s in the router %s", mac, target.upper(),
                            self._ip_address)
        return statistics
