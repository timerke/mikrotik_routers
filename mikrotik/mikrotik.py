import logging
from typing import Dict, List, Tuple
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

    @staticmethod
    def _get_mac_and_target(item: Dict[str, str]) -> Dict[str, str]:
        """
        Method returns MAC address and target (SRC or DST) of given filter.
        :param item: data for given filter from router.
        :return: dictionary with MAC address and target (SRC or DST).
        """

        src_mac = item.get("src-mac-address", None)
        dst_mac = item.get("dst-mac-address", None)
        if src_mac is not None:
            data = {"mac": src_mac.split("/")[0].upper(),
                    "target": "SRC"}
        elif dst_mac is not None:
            data = {"mac": dst_mac.split("/")[0].upper(),
                    "target": "DST"}
        else:
            data = {"mac": "",
                    "target": ""}
        return data

    def _get_total_statistics(self) -> List[Dict[str, str]]:
        """
        Method gets filter statistics from router.
        :return: list of dictionaries with MAC address of filter, target of filter, state of filter
        and comment.
        """

        result = self._router.talk("/interface/bridge/filter/print")
        statistics = []
        for item in result:
            data = {"action": item.get("action", ""),
                    "disabled": item.get("disabled", ""),
                    "comment": item.get("comment", "")}
            data.update(**self._get_mac_and_target(item))
            statistics.append(data)
        return statistics

    def add_comment(self, mac_address: str, target: str, comment: str) -> bool:
        """
        Method adds comment to filter.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        :return: True if comment was added.
        """

        indices = []
        for index, filter_data in enumerate(self._get_total_statistics()):
            if filter_data["mac"] == mac_address and filter_data["target"] == target:
                indices.append(str(index))
        if indices:
            self._router.talk(("/interface/bridge/filter/comment", f"=comment={comment}",
                               f"=numbers={','.join(indices)}"))
            return True
        return False

    def add_filter(self, mac_address: str, target: str, comment: str) -> None:
        """
        Method adds new filter to router.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        """

        if comment:
            self._router.talk(("/interface/bridge/filter/add", "=action=accept", "=chain=forward", "=disabled=false",
                               f"={target.lower()}-mac-address={mac_address}/FF:FF:FF:FF:FF:FF",
                               f"=comment={comment}"))
        else:
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
        :return: True if filter is removed.
        """

        statistics = self._get_total_statistics()
        statistics.reverse()
        filter_was_deleted = False
        for index, filter_data in enumerate(statistics):
            if filter_data["mac"] == mac_address and filter_data["target"] == target:
                self._router.talk(f"/interface/bridge/filter/remove\n=numbers={len(statistics) - index - 1}")
                filter_was_deleted = True
        return filter_was_deleted

    def enable_filter(self, mac_address: str, target: str, state: str) -> None:
        """
        Method enables or disables some filter on router.
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param state: enable or disable.
        """

        for index, filter_data in enumerate(self._get_total_statistics()):
            if filter_data["mac"] == mac_address and filter_data["target"] == target:
                self._router.talk(f"/interface/bridge/filter/{state}\n=numbers={index}")
                break

    def get_indices_of_drop_filters(self) -> List[int]:
        """
        Method returns indices of drop filters.
        :return: indices of drop filters.
        """

        indices = []
        for filter_index, filter_data in enumerate(self._get_total_statistics()):
            if filter_data["action"] == "drop":
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
        for filter_index, filter_data in enumerate(self._get_total_statistics()):
            if filter_data["mac"] == mac_address and filter_data["target"] == target:
                indices.append(filter_index)
        return indices

    def get_statistics(self) -> Dict[Tuple[str, str], Dict[str, str]]:
        """
        Method receives filter statistics from router.
        :return: list with filter statistics.
        """

        statistics = {}
        multiple_filters = set()
        for filter_data in self._get_total_statistics():
            if not filter_data["target"]:
                continue
            if (filter_data["mac"], filter_data["target"]) not in statistics:
                statistics[(filter_data["mac"], filter_data["target"])] = {"comment": filter_data["comment"],
                                                                           "disabled": filter_data["disabled"]}
            else:
                multiple_filters.add((filter_data["mac"], filter_data["target"]))
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
