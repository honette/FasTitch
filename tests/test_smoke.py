from pathlib import Path

import pytest
from PIL import Image

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from fastitch.app import MainWindow
from fastitch.config import Settings
from fastitch.constants import APP_NAME
from fastitch.imageops import load_image


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _png(path: Path, width: int, height: int, color: tuple[int, int, int]) -> Path:
    Image.new("RGB", (width, height), color).save(path)
    return path


def test_load_stitch_save_roundtrip(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "a.png", 40, 100, (255, 0, 0))
    b = _png(tmp_path / "b.png", 80, 100, (0, 255, 0))
    settings = Settings(last_dir=str(tmp_path), output_format="png")
    window = MainWindow(settings)
    window.show()
    qapp.processEvents()
    window.add_paths([a, b])
    assert window.windowTitle().startswith(APP_NAME)
    assert window._result is not None
    assert window._result.size == (120, 100)
    assert window.list.count() == 2
    assert window.save_btn.isEnabled()
    window.save_result()
    saved = tmp_path / "a_stitched.png"
    assert saved.exists()
    out = load_image(saved)
    assert out.size == (120, 100)
    window.close()


def test_first_too_wide_disables_save(qapp: QApplication, tmp_path: Path) -> None:
    wide = _png(tmp_path / "wide.png", 2000, 900, (1, 2, 3))
    window = MainWindow(Settings(last_dir=str(tmp_path)))
    window.show()
    qapp.processEvents()
    window.add_paths([wide])
    assert window._error is not None
    assert "16:9" in window._error
    assert not window.save_btn.isEnabled()
    window.close()


def test_reorder_changes_first_and_height(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "short.png", 40, 40, (255, 0, 0))
    b = _png(tmp_path / "tall.png", 40, 80, (0, 255, 0))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a, b])
    assert window._result is not None
    assert window._result.size == (60, 40)
    window.list.setCurrentRow(0)
    window._move_selected(1)
    qapp.processEvents()
    assert window._items[0].path.name == "tall.png"
    assert window._result is not None
    assert window._result.size == (120, 80)
    window.close()


def test_drop_mime_and_title(qapp: QApplication, tmp_path: Path) -> None:
    from PySide6.QtCore import QMimeData, QUrl

    from fastitch.dnd import dropped_image_paths

    source = _png(tmp_path / "dropme.png", 32, 32, (1, 2, 3))
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(source))])
    assert dropped_image_paths(mime) == [source]

    window = MainWindow(Settings())
    assert window.windowTitle() == APP_NAME
    assert APP_NAME == "FasTitch"
    window.close()


def test_dialogs_construct(qapp: QApplication) -> None:
    from fastitch.dialogs import SettingsDialog, ShortcutsDialog

    settings = Settings()
    dialog = SettingsDialog(settings)
    dialog.apply_to(settings)
    assert settings.output_format == "jpeg"
    dialog.close()
    ShortcutsDialog().close()


def test_save_collision_uses_number(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "shot.png", 50, 100, (10, 10, 10))
    b = _png(tmp_path / "other.png", 50, 100, (20, 20, 20))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a, b])
    window.save_result()
    window.save_result()
    assert (tmp_path / "shot_stitched.png").exists()
    assert (tmp_path / "shot_stitched_2.png").exists()
    window.close()


def test_copy_button_copies_stitched_image(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "a.png", 40, 100, (255, 0, 0))
    b = _png(tmp_path / "b.png", 80, 100, (0, 255, 0))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a, b])
    assert window.copy_btn.isEnabled()
    assert window.copy_act.isEnabled()

    window.copy_btn.click()
    qapp.processEvents()

    from PySide6.QtGui import QGuiApplication

    clipboard = QGuiApplication.clipboard()
    assert clipboard is not None
    image = clipboard.image()
    assert (image.width(), image.height()) == (120, 100)
    assert image.pixelColor(0, 0).red() == 255
    assert image.pixelColor(119, 99).green() == 255
    assert "Copied" in window.msg_label.text()
    window.close()


def test_copy_disabled_when_error(qapp: QApplication, tmp_path: Path) -> None:
    wide = _png(tmp_path / "wide.png", 2000, 900, (1, 2, 3))
    window = MainWindow(Settings(last_dir=str(tmp_path)))
    window.add_paths([wide])
    assert window._error is not None
    assert not window.copy_btn.isEnabled()
    assert not window.copy_act.isEnabled()
    window.copy_result()
    assert "Copied" not in window.msg_label.text()
    window.close()


def test_row_delete_button_removes_item(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "one.png", 40, 100, (255, 0, 0))
    b = _png(tmp_path / "two.png", 80, 100, (0, 255, 0))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a, b])
    assert window.list.count() == 2

    row = window.list.itemWidget(window.list.item(0))
    assert row is not None
    row.remove_btn.click()
    qapp.processEvents()

    assert window.list.count() == 1
    assert [item.path.name for item in window._items] == ["two.png"]
    assert window._result is not None
    assert window._result.size == (80, 100)
    window.close()


def test_row_delete_button_matches_remove_selected(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "one.png", 40, 100, (255, 0, 0))
    b = _png(tmp_path / "two.png", 80, 100, (0, 255, 0))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a, b])
    window.list.setCurrentRow(1)
    window.remove_selected()
    expected = [(item.path.name, item.key) for item in window._items]
    window.clear_items()

    window.add_paths([a, b])
    row = window.list.itemWidget(window.list.item(1))
    row.remove_btn.click()
    qapp.processEvents()

    assert [(item.path.name, item.key) for item in window._items] == expected
    assert window.list.count() == 1
    assert window.list.currentRow() == 0
    window.close()


def test_delete_key_removes_current_item(qapp: QApplication, tmp_path: Path) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

    a = _png(tmp_path / "one.png", 40, 100, (255, 0, 0))
    b = _png(tmp_path / "two.png", 80, 100, (0, 255, 0))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a, b])
    window.list.setCurrentRow(0)
    window.list.keyPressEvent(
        QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    )
    qapp.processEvents()
    assert [item.path.name for item in window._items] == ["two.png"]
    window.close()


def test_row_is_compact(qapp: QApplication, tmp_path: Path) -> None:
    a = _png(tmp_path / "one.png", 40, 100, (255, 0, 0))
    window = MainWindow(Settings(last_dir=str(tmp_path), output_format="png"))
    window.add_paths([a])
    row = window.list.itemWidget(window.list.item(0))
    assert row is not None
    assert row.remove_btn.width() <= 16 and row.remove_btn.height() <= 16
    assert row.sizeHint().width() - row.thumb.width() <= 120
    assert window.list.item(0).sizeHint().height() <= 96
    window.close()


def test_delete_icon_is_an_x(qapp: QApplication, tmp_path: Path) -> None:
    from fastitch.app import make_delete_icon

    image = make_delete_icon(64).pixmap(64, 64).toImage()
    assert image.pixelColor(32, 32).alpha() > 40
    assert image.pixelColor(6, 32).alpha() == 0
    assert image.pixelColor(58, 32).alpha() == 0
    assert image.pixelColor(32, 6).alpha() == 0
    assert image.pixelColor(32, 58).alpha() == 0
    assert image.pixelColor(0, 0).alpha() == 0
