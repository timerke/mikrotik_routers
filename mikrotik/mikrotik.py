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

    def _get_total_statistics(self) -> List[Tuple[str, str, Optional[str], str]]:
        """
        Method gets filter statistics from router.
        :return: list with MAC address of filter, target of filter and state of filter.
        """

        result = self._router.talk("/interface/bridge/filter/print")
        statistics = []
        for item in result:
            mac = ""
            target = ""
            action = item.get("action", "")
            disabled = item.get("disabled", "")
            src_mac = item.get("src-mac-address", None)
            dst_mac = item.get("dst-mac-address", None)
            if src_mac is not None:
                mac = src_mac.split("/")[0]
                target = "SRC"
            if dst_mac is not None:
                mac = dst_mac.split("/")[0]
                target = "DST"
            statistics.append((mac.upper(), target.upper(), disabled, action))
        return statistics

    def add_filter(self, mac_address: str, target: str) -> None:
        """
        Method adds new filter to router.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        """

        self._router.talk(f"/interface/bridge/filter/add\n=action=accept\n=chain=forward\n=disabled=false"
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
        for index, (mac_item, target_item, _, _) in enumerate(statistics):
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

        for index, (mac_item, target_item, _, _) in enumerate(self._get_total_statistics()):
            if mac_item == mac_address and target_item == target:
                self._router.talk(f"/interface/bridge/filter/{state}\n=numbers={index}")
                break

    def get_indices_of_drop_filters(self) -> List[int]:
        """
        Method returns indices if drop filters.
        :return: indices of drop filters.
        """

        indices = []
        for filter_index, (_, _, _, action) in enumerate(self._get_total_statistics()):
            if action.lower() == "drop":
                indices.append(filter_index)
        return indices

    def get_indices_of_filter(self, mac_address: str, target: str) -> List[int]:
        """
        Method returns indices of filter.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter.
        :return: lists of indices of filters.
        """

        indices = []
        for filter_index, (filter_mac, filter_target, _, _) in enumerate(self._get_total_statistics()):
            if filter_mac == mac_address and filter_target == target:
                indices.append(filter_index)
        return indices

    def get_statistics(self) -> Dict[Tuple[str, str], Optional[str]]:
        """
        Method receives filter statistics from router.
        :return: list with filter statistics.
        """

        statistics = {}
        multiple_filters = set()
        for mac, target, disabled, _ in self._get_total_statistics():
            if not target:
                continue
            if (mac, target) not in statistics:
                statistics[(mac, target)] = disabled
            else:
                multiple_filters.add((mac, target))
        for mac, target in multiple_filters:
            logging.warning("There are several filters %s %s in the router %s", mac, target.upper(), self._ip_address)
        return statistics

    def move_filter(self, index_from: int, index_to: int) -> None:
        """
        Method moves filter in list of filters.
        :param index_from: index of filter to be moved;
        :param index_to: position index where to move filter.
        """

        self._router.talk(f"/interface/bridge/filter/move\n=destination={index_to}\n=numbers={index_from}")
