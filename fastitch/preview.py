from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QLabel

from fastitch.dnd import dropped_image_paths


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    if image.mode == "RGB":
        data = image.tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format_RGB888)
    else:
        converted = image.convert("RGBA")
        data = converted.tobytes("raw", "RGBA")
        qimage = QImage(
            data,
            converted.width,
            converted.height,
            converted.width * 4,
            QImage.Format_RGBA8888,
        )
    return QPixmap.fromImage(qimage.copy())


def copy_to_clipboard(image: Image.Image) -> bool:
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return False
    pixmap = pil_to_qpixmap(image)
    clipboard.setPixmap(pixmap)
    clipboard.setImage(pixmap.toImage())
    return True


class PreviewView(QGraphicsView):
    filesDropped = Signal(object)

    def __init__(self, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFrameShape(QFrame.NoFrame)
        self.setBackgroundBrush(QColor("#121212"))
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self._pix_item: QGraphicsPixmapItem | None = None

        self._empty = QLabel("Drop images here", self.viewport())
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setWordWrap(True)
        self._empty.setStyleSheet("color: #8a8a8a; font-size: 16px; background: transparent; padding: 24px;")
        self._empty.setAttribute(Qt.WA_TransparentForMouseEvents)

    def clear_preview(self, message: str = "Drop images here") -> None:
        self._scene.clear()
        self._pix_item = None
        self._empty.setText(message)
        self._empty.show()
        self._empty.setGeometry(self.viewport().rect())

    def set_result(self, pixmap: QPixmap, dividers: tuple[int, ...] | list[int]) -> None:
        self._scene.clear()
        self._pix_item = self._scene.addPixmap(pixmap)
        self._pix_item.setZValue(0)
        height = pixmap.height()
        pen = QPen(QColor(255, 255, 255, 140), 0)
        for x in dividers:
            self._scene.addLine(x, 0, x, height, pen)
        self._scene.setSceneRect(QRectF(0, 0, pixmap.width(), height))
        self._empty.hide()
        self._fit()

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self._empty.setGeometry(self.viewport().rect())
        self._fit()

    def _fit(self) -> None:
        if self._pix_item is None:
            return
        self.fitInView(self._pix_item, Qt.KeepAspectRatio)

    def dragEnterEvent(self, event) -> None:  # noqa: ANN001
        if dropped_image_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: ANN001
        if dropped_image_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: ANN001
        paths = dropped_image_paths(event.mimeData())
        if not paths:
            event.ignore()
            return
        self.filesDropped.emit(paths)
        event.acceptProposedAction()
