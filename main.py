"""
File to start GUI application.
"""

import sys
import traceback
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from gui.logger import logger
from gui.main_window import MainWindow
from gui.utils import show_exception


class ExceptionHandler(QObject):
    """
    Class to handle unexpected errors.
    """

    exception_raised: pyqtSignal = pyqtSignal(str, str, str)

    def exception_hook(self, exc_type: Exception, exc_value: Exception, exc_traceback: "traceback") -> None:
        """
        Method handles unexpected errors.
        :param exc_type: exception class;
        :param exc_value: exception instance;
        :param exc_traceback: traceback object.
        """

        traceback.print_exception(exc_type, exc_value, exc_traceback)
        traceback_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        full_msg_text = (f"Произошла ошибка. Сфотографируйте сообщение с ошибкой и обратитесь в техподдержку.\n\n"
                         f"{str(exc_value)}")
        self.exception_raised.emit("Error", full_msg_text, traceback_text)


if __name__ == "__main__":
    logger
    app = QApplication(sys.argv)
    exceprion_handler = ExceptionHandler()
    sys.excepthook = exceprion_handler.exception_hook
    exceprion_handler.exception_raised.connect(show_exception)
    main_window = MainWindow()
    main_window.show()
    app.exec()
