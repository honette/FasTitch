from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from fastitch.config import Settings
from fastitch.constants import OUTPUT_FORMATS
from fastitch.imageops import ext_for_format
from fastitch.naming import example_name


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, sample_name: str = "IMG_1234.jpg", parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._sample = sample_name

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.suffix = QLineEdit(settings.suffix)
        self.suffix.setPlaceholderText("_stitched")
        form.addRow("Filename suffix", self.suffix)

        self.subfolder = QLineEdit(settings.subfolder)
        self.subfolder.setPlaceholderText("Empty = same folder as first image")
        form.addRow("Subfolder", self.subfolder)

        self.output_format = QComboBox()
        for label, value in OUTPUT_FORMATS:
            self.output_format.addItem(label, value)
        index = self.output_format.findData(settings.output_format)
        self.output_format.setCurrentIndex(max(0, index))
        form.addRow("Output format", self.output_format)

        self.quality = QSpinBox()
        self.quality.setRange(1, 100)
        self.quality.setValue(settings.jpeg_quality)
        self.quality.setSuffix(" %")
        form.addRow("JPEG / WebP quality", self.quality)
        layout.addLayout(form)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet("color: #9cdcfe;")
        layout.addWidget(self.preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        for widget in (self.suffix, self.subfolder):
            widget.textChanged.connect(self._refresh_preview)
        self.output_format.currentIndexChanged.connect(self._refresh_preview)
        self._refresh_preview()
        self.resize(460, 260)

    def apply_to(self, settings: Settings) -> None:
        settings.suffix = self.suffix.text().strip() or settings.suffix
        settings.subfolder = self.subfolder.text().strip()
        settings.output_format = str(self.output_format.currentData())
        settings.jpeg_quality = self.quality.value()

    def _refresh_preview(self) -> None:
        ext = ext_for_format(str(self.output_format.currentData() or "jpeg"))
        name = example_name(
            self._sample,
            suffix=self.suffix.text(),
            subfolder=self.subfolder.text(),
            ext=ext,
        )
        self.preview.setText(f"Preview: {name}")


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Keyboard shortcuts")
        layout = QVBoxLayout(self)
        text = QLabel(
            "\n".join(
                [
                    "Ctrl+O            Open images (replace list)",
                    "Ctrl+Shift+O      Add images",
                    "Ctrl+S            Save",
                    "Delete            Remove selected",
                    "Ctrl+Up / Down    Move selected",
                    "Drop files        Append to list",
                ]
            )
        )
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
