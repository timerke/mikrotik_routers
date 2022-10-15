import os
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox


DIR_MEDIA: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")


def get_dir_name() -> str:
    """
    Function returns path to directory with executable file or code files.
    :return: path to directory.
    """

    if getattr(sys, "frozen", False):
        path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return path


def show_exception(msg_title: str, msg_text: str, exc: str = "") -> None:
    """
    Function shows message box with error.
    :param msg_title: title of message box;
    :param msg_text: message text;
    :param exc: text of exception.
    """

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(msg_title)
    msg_box.setWindowIcon(QIcon(os.path.join(DIR_MEDIA, "icon.png")))
    msg_box.setText(msg_text)
    if exc:
        msg_box.setInformativeText(str(exc)[-500:])
    msg_box.exec_()
