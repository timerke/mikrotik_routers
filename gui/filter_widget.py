from typing import Optional, Tuple
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class FilterWidget(QWidget):
    """
    Class to show data about filter.
    """

    MAX_COMMENT_LENGTH: int = 25

    def __init__(self, mac_address: str, target: str, comment: Optional[str] = "") -> None:
        """
        :param mac_address: MAC address of filter;
        :param target: target (SRC or DST) of filter;
        :param comment: comment for filter.
        """

        super().__init__()
        self._mac_address: str = mac_address
        self._target: str = target
        self._comment: str = comment

        self.label_base: QLabel = QLabel(f"{mac_address} {target}")
        self.label_base.setStyleSheet("color: blue")
        self.label_comment: QLabel = QLabel()
        self.label_comment.setStyleSheet("color: green")
        self.set_comment(comment)
        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label_base)
        layout.addWidget(self.label_comment)
        self.setLayout(layout)

    @property
    def comment(self) -> str:
        """
        :return: comment of filter.
        """

        return self._comment

    @property
    def mac_address(self) -> str:
        """
        :return: MAC address of filter.
        """

        return self._mac_address

    @property
    def target(self) -> str:
        """
        :return: target (SRC or DST) of filter.
        """

        return self._target

    def get_data(self) -> Tuple[str, str, str]:
        """
        :return: :return: MAC address, target (SRC or DST) and comment of filter.
        """

        return self.mac_address, self.target, self.comment

    def get_filter_name(self) -> str:
        """
        :return: MAC address and target (SRC or DST) of filter in string format.
        """

        return f"{self.mac_address} {self.target}"

    def get_mac_address_and_target(self) -> Tuple[str, str]:
        """
        :return: MAC address and target (SRC or DST) of filter.
        """

        return self.mac_address, self.target

    def set_comment(self, comment: str) -> None:
        """
        Method sets new comment for filter.
        :param comment: comment for filter.
        """

        self._comment = comment
        self.label_comment.setText(comment[:self.MAX_COMMENT_LENGTH])
        self.label_comment.setVisible(bool(comment))
