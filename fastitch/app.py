from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QLocale, QSize, QStandardPaths, Qt, QUrl, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QIcon,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from fastitch import __version__
from fastitch.config import Settings, load_settings, save_settings
from fastitch.constants import APP_NAME, OPEN_FILTER, ORG_NAME
from fastitch.dialogs import SettingsDialog, ShortcutsDialog
from fastitch.dnd import dropped_image_paths
from fastitch.geom import StitchError, StitchPlan
from fastitch.imageops import collect_image_paths, ext_for_format, is_image_file, load_image, render_stitch, save_image
from fastitch.naming import example_name, next_dest_path
from fastitch.preview import PreviewView, copy_to_clipboard, pil_to_qpixmap
from fastitch.theme import apply_theme, make_app_icon

THUMB_SIZE = 96


@dataclass
class StitchItem:
    path: Path
    image: Image.Image
    key: str


REMOVE_ICON_SIZE = 14
REMOVE_BTN_SIZE = 16


def make_delete_icon(size: int = REMOVE_ICON_SIZE) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#e8e8e8"), max(1.3, size / 9))
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    inset = size * 0.3
    painter.drawLine(int(inset), int(inset), int(size - inset), int(size - inset))
    painter.drawLine(int(size - inset), int(inset), int(inset), int(size - inset))
    painter.end()
    return QIcon(pixmap)


class ThumbRow(QWidget):
    removed = Signal()

    def __init__(self, icon: QIcon, text: str, tooltip: str, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.thumb = QLabel()
        self.thumb.setPixmap(icon.pixmap(QSize(THUMB_SIZE, THUMB_SIZE)))
        self.thumb.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        self.thumb.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.thumb)
        self.name = QLabel(text)
        self.name.setWordWrap(True)
        self.name.setContentsMargins(6, 0, 0, 0)
        self.name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name, 1)
        self.remove_btn = QToolButton()
        self.remove_btn.setObjectName("thumbRemoveBtn")
        self.remove_btn.setIcon(make_delete_icon())
        self.remove_btn.setIconSize(QSize(REMOVE_ICON_SIZE, REMOVE_ICON_SIZE))
        self.remove_btn.setAutoRaise(True)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setToolTip("Remove")
        self.remove_btn.setFixedSize(REMOVE_BTN_SIZE, REMOVE_BTN_SIZE)
        self.remove_btn.clicked.connect(self.removed)
        layout.addWidget(self.remove_btn, 0, Qt.AlignVCenter)
        self.setToolTip(tooltip)


class ThumbList(QListWidget):
    orderChanged = Signal()
    filesDropped = Signal(object)
    removeRequested = Signal(str)

    def __init__(self, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))
        self.setSpacing(4)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrap(True)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # noqa: ANN001
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # noqa: ANN001
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: ANN001
        if event.mimeData().hasUrls():
            paths = dropped_image_paths(event.mimeData())
            if paths:
                self.filesDropped.emit(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)
        self.orderChanged.emit()

    def keyPressEvent(self, event) -> None:  # noqa: ANN001
        if event.key() in (Qt.Key_Delete,):
            key = self._current_key()
            if key:
                self.removeRequested.emit(key)
                event.accept()
                return
        super().keyPressEvent(event)

    def _current_key(self) -> str:
        item = self.currentItem()
        if item is None:
            return ""
        return str(item.data(Qt.UserRole) or "")


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self.settings = settings or load_settings()
        self._items: list[StitchItem] = []
        self._result: Image.Image | None = None
        self._plan: StitchPlan | None = None
        self._error: str | None = None

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(make_app_icon())
        self.setAcceptDrops(True)
        self.resize(self.settings.window_w, self.settings.window_h)
        if self.settings.window_x >= 0 and self.settings.window_y >= 0:
            self.move(self.settings.window_x, self.settings.window_y)

        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self._rebuild()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_act = QAction("&Open…", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self.open_dialog)
        file_menu.addAction(open_act)

        add_act = QAction("&Add…", self)
        add_act.setShortcut(QKeySequence("Ctrl+Shift+O"))
        add_act.triggered.connect(self.add_dialog)
        file_menu.addAction(add_act)

        self.remove_act = QAction("&Remove selected", self)
        self.remove_act.setShortcut(QKeySequence.Delete)
        self.remove_act.triggered.connect(self.remove_selected)
        file_menu.addAction(self.remove_act)

        clear_act = QAction("&Clear", self)
        clear_act.triggered.connect(self.clear_items)
        file_menu.addAction(clear_act)
        file_menu.addSeparator()

        self.save_act = QAction("&Save", self)
        self.save_act.setShortcut(QKeySequence.Save)
        self.save_act.triggered.connect(self.save_result)
        file_menu.addAction(self.save_act)

        self.copy_act = QAction("&Copy image", self)
        self.copy_act.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.copy_act.triggered.connect(self.copy_result)
        file_menu.addAction(self.copy_act)

        folder_act = QAction("Open &folder", self)
        folder_act.triggered.connect(self.open_current_folder)
        file_menu.addAction(folder_act)
        file_menu.addSeparator()

        settings_act = QAction("&Settings…", self)
        settings_act.triggered.connect(self.open_settings)
        file_menu.addAction(settings_act)
        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        help_menu = self.menuBar().addMenu("&Help")
        shortcut_act = QAction("&Keyboard shortcuts", self)
        shortcut_act.triggered.connect(lambda: ShortcutsDialog(self).exec())
        help_menu.addAction(shortcut_act)
        about_act = QAction("&About", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setAcceptDrops(True)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_ribbon())

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self._build_sidebar())
        self.preview = PreviewView()
        self.preview.filesDropped.connect(self.add_paths)
        self.splitter.addWidget(self.preview)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        if self.settings.splitter and len(self.settings.splitter) == 2:
            self.splitter.setSizes(self.settings.splitter)
        root_layout.addWidget(self.splitter, 1)
        self.setCentralWidget(root)

        status = QStatusBar()
        self.setStatusBar(status)
        self.count_label = QLabel("0 images")
        self.size_label = QLabel("Size: —")
        self.msg_label = QLabel("")
        self.msg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status.addWidget(self.count_label)
        status.addWidget(self.size_label)
        status.addWidget(self.msg_label, 1)

    def _build_ribbon(self) -> QFrame:
        ribbon = QFrame()
        ribbon.setObjectName("ribbon")
        layout = QHBoxLayout(ribbon)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_dialog)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_dialog)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_items)
        layout.addWidget(open_btn)
        layout.addWidget(add_btn)
        layout.addWidget(self.remove_btn)
        layout.addWidget(clear_btn)
        layout.addStretch(1)
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setToolTip("Copy the stitched image to the clipboard")
        self.copy_btn.clicked.connect(self.copy_result)
        layout.addWidget(self.copy_btn)
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("cropSaveBtn")
        self.save_btn.clicked.connect(self.save_result)
        layout.addWidget(self.save_btn)
        return ribbon

    def _build_sidebar(self) -> QFrame:
        side = QFrame()
        side.setObjectName("sidebar")
        side.setMinimumWidth(180)
        side.setMaximumWidth(360)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(8, 8, 8, 8)
        self.sidebar_title = QLabel("Images")
        self.sidebar_title.setObjectName("sidebarTitle")
        layout.addWidget(self.sidebar_title)
        self.list = ThumbList()
        self.list.orderChanged.connect(self._on_order_changed)
        self.list.filesDropped.connect(self.add_paths)
        self.list.removeRequested.connect(self.remove_key)
        self.list.currentRowChanged.connect(self._update_actions)
        layout.addWidget(self.list, 1)
        return side

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Up"), self, lambda: self._move_selected(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self, lambda: self._move_selected(1))

    def open_dialog(self) -> None:
        paths = self._pick_files("Open images")
        if paths:
            self.add_paths(paths, replace=True)

    def add_dialog(self) -> None:
        paths = self._pick_files("Add images")
        if paths:
            self.add_paths(paths)

    def _pick_files(self, title: str) -> list[Path]:
        start = self.settings.last_dir or QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        files, _ = QFileDialog.getOpenFileNames(self, title, start, OPEN_FILTER)
        return [Path(p) for p in files]

    def add_paths(self, paths, replace: bool = False) -> None:  # noqa: ANN001
        collected = collect_image_paths([Path(p) for p in paths])
        if replace:
            self._items = []
            self.list.clear()
        existing = {item.key for item in self._items}
        skipped = 0
        errors: list[str] = []
        added = 0
        for path in collected:
            try:
                key = str(path.resolve())
            except OSError:
                key = str(path)
            if key in existing:
                skipped += 1
                continue
            try:
                image = load_image(path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path.name}: {exc}")
                continue
            item = StitchItem(path=path, image=image, key=key)
            self._items.append(item)
            existing.add(key)
            self._append_list_item(item)
            added += 1
            self.settings.last_dir = str(path.parent)
        if added:
            save_settings(self.settings)
        self._rebuild()
        bits: list[str] = []
        if added:
            bits.append(f"Added {added}")
        if skipped:
            bits.append(f"skipped {skipped} duplicate(s)")
        if errors:
            QMessageBox.warning(self, APP_NAME, "Could not open:\n" + "\n".join(errors[:8]))
        if bits:
            self.msg_label.setText(", ".join(bits))

    def _append_list_item(self, item: StitchItem) -> None:
        thumb = item.image.copy()
        thumb.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
        list_item = QListWidgetItem()
        list_item.setData(Qt.UserRole, item.key)
        list_item.setToolTip(str(item.path))
        self.list.addItem(list_item)
        row = ThumbRow(QIcon(pil_to_qpixmap(thumb)), item.path.name, str(item.path))
        row.removed.connect(lambda key=item.key: self.remove_key(key))
        list_item.setSizeHint(row.sizeHint())
        self.list.setItemWidget(list_item, row)

    def _on_order_changed(self) -> None:
        by_key = {item.key: item for item in self._items}
        ordered: list[StitchItem] = []
        for i in range(self.list.count()):
            key = str(self.list.item(i).data(Qt.UserRole))
            found = by_key.get(key)
            if found is not None:
                ordered.append(found)
        if len(ordered) == len(self._items):
            self._items = ordered
        self._rebuild()

    def _move_selected(self, delta: int) -> None:
        row = self.list.currentRow()
        new_row = row + delta
        if row < 0 or not (0 <= new_row < self.list.count()):
            return
        item = self.list.takeItem(row)
        self.list.insertItem(new_row, item)
        self.list.setCurrentRow(new_row)
        self._on_order_changed()

    def remove_selected(self) -> None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self._items):
            return
        self._remove_row(row)

    def remove_key(self, key: str) -> None:
        for row, item in enumerate(self._items):
            if item.key == key:
                self._remove_row(row)
                return

    def _remove_row(self, row: int) -> None:
        if not (0 <= row < self.list.count()):
            return
        self.list.takeItem(row)
        if 0 <= row < len(self._items):
            del self._items[row]
        if self.list.count():
            self.list.setCurrentRow(min(row, self.list.count() - 1))
        self._rebuild()

    def clear_items(self) -> None:
        self._items = []
        self.list.clear()
        self._rebuild()

    def _rebuild(self) -> None:
        self._result = None
        self._plan = None
        self._error = None
        count = len(self._items)
        self.sidebar_title.setText(f"Images ({count})")
        if not self._items:
            self.preview.clear_preview("Drop images here")
            self._update_status()
            self._update_actions()
            self.setWindowTitle(APP_NAME)
            return
        try:
            image, plan = render_stitch([item.image for item in self._items])
        except StitchError as exc:
            self._error = str(exc)
            self.preview.clear_preview(str(exc))
            self._update_status()
            self._update_actions()
            self.setWindowTitle(APP_NAME)
            return
        self._result = image
        self._plan = plan
        self.preview.set_result(pil_to_qpixmap(image), plan.divider_xs)
        self.setWindowTitle(f"{APP_NAME} — {count} images ({image.width}x{image.height})")
        self._update_status()
        self._update_actions()

    def _update_status(self) -> None:
        count = len(self._items)
        self.count_label.setText(f"{count} image" if count == 1 else f"{count} images")
        if self._error:
            self.size_label.setText("Size: —")
            self.msg_label.setText(self._error)
            return
        if self._result is None or self._plan is None:
            self.size_label.setText("Size: —")
            self.msg_label.setText("")
            return
        dest_hint = self._dest_hint()
        if self._plan.trimmed:
            before = sum(panel.scaled_width for panel in self._plan.panels)
            self.size_label.setText(
                f"{before}x{self._plan.height} → {self._result.width}x{self._result.height}"
            )
        else:
            self.size_label.setText(f"{self._result.width}x{self._result.height} (no trim)")
        self.msg_label.setText(f"Save to: {dest_hint}" if dest_hint else "")

    def _dest_hint(self) -> str:
        if not self._items:
            return ""
        ext = ext_for_format(self.settings.output_format)
        return example_name(
            self._items[0].path.name,
            suffix=self.settings.suffix,
            subfolder=self.settings.subfolder,
            ext=ext,
        )

    def _update_actions(self) -> None:
        has_sel = self.list.currentRow() >= 0
        can_save = self._result is not None and self._error is None
        self.remove_btn.setEnabled(has_sel)
        self.remove_act.setEnabled(has_sel)
        self.copy_btn.setEnabled(can_save)
        self.save_btn.setEnabled(can_save)
        self.save_act.setEnabled(can_save)
        self.copy_act.setEnabled(can_save)

    def copy_result(self) -> None:
        if self._result is None or self._error:
            return
        if copy_to_clipboard(self._result):
            self.msg_label.setText(f"Copied {self._result.width}x{self._result.height} to clipboard")
        else:
            self.msg_label.setText("Could not copy to clipboard")

    def save_result(self) -> None:
        if self._error:
            QMessageBox.warning(self, APP_NAME, self._error)
            return
        if self._result is None or not self._items:
            return
        first = self._items[0].path
        ext = ext_for_format(self.settings.output_format)
        dest = next_dest_path(
            first,
            suffix=self.settings.suffix,
            subfolder=self.settings.subfolder,
            ext=ext,
        )
        try:
            save_image(self._result, dest, jpeg_quality=self.settings.jpeg_quality)
        except OSError as exc:
            QMessageBox.warning(self, APP_NAME, f"Could not save:\n{exc}")
            return
        self.msg_label.setText(f"Saved: {dest}")

    def open_current_folder(self) -> None:
        if self._items:
            folder = self._items[0].path.parent
        else:
            folder = Path(self.settings.last_dir or ".")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def open_settings(self) -> None:
        sample = self._items[0].path.name if self._items else "IMG_1234.jpg"
        dialog = SettingsDialog(self.settings, sample, self)
        if dialog.exec():
            dialog.apply_to(self.settings)
            save_settings(self.settings)
            self._update_status()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            APP_NAME,
            f"{APP_NAME} {__version__}\n\n"
            "Drop images, stitch them left to right, save one file.",
        )

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
        self.add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: ANN001
        geo = self.geometry()
        self.settings.window_x = geo.x()
        self.settings.window_y = geo.y()
        self.settings.window_w = geo.width()
        self.settings.window_h = geo.height()
        self.settings.splitter = self.splitter.sizes()
        save_settings(self.settings)
        super().closeEvent(event)


def main() -> None:
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setWindowIcon(make_app_icon())
    apply_theme(app)
    window = MainWindow()
    window.show()
    paths = [Path(arg) for arg in sys.argv[1:] if not arg.startswith("-")]
    images = [path for path in paths if is_image_file(path) or path.is_dir()]
    if images:
        window.add_paths(images)
    sys.exit(app.exec())
