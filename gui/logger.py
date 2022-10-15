import logging
from PyQt5.QtCore import pyqtSignal, QObject


class LoggingHandler(logging.Handler):
    """
    Class to send logs from logging module by PyQt5 signals.
    """

    class LoggingForwarder(QObject):
        log_received: pyqtSignal = pyqtSignal(str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._forwarder: self.LoggingForwarder = self.LoggingForwarder()

    @property
    def log_received(self) -> pyqtSignal:
        return self._forwarder.log_received

    def emit(self, record: logging.LogRecord) -> None:
        self._forwarder.log_received.emit(record.asctime, record.levelname, record.message)


formatter = logging.Formatter("[%(asctime)s - %(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)
logger.propagate = False
