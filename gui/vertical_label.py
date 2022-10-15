from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPainter, QPaintEvent
from PyQt5.QtWidgets import QLabel


class VerticalLabel(QLabel):
    """
    Class for displaying text vertically.
    https://stackoverflow.com/questions/3757246/pyqt-rotate-a-qlabel-so-that-its-positioned-diagonally-
    instead-of-horizontally
    """

    def __init__(self, *args) -> None:
        QLabel.__init__(self, *args)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.translate(0, self.height())
        painter.rotate(-90)
        painter.drawText(0, self.width() // 2, self.text())
        painter.end()

    def minimumSizeHint(self) -> QSize:
        size = QLabel.minimumSizeHint(self)
        return QSize(size.height(), size.width())

    def sizeHint(self) -> QSize:
        size = QLabel.sizeHint(self)
        return QSize(size.height(), size.width())
