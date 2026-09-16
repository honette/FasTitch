import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(autouse=True)
def fastitch_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FASTITCH_CONFIG_DIR", str(tmp_path / "fastitch-config"))
