# AGENTS.md

このファイルは、このリポジトリで作業するAIコーディングエージェントへの指示です。

## プロジェクト概要

FasTitch は複数画像を右方向へ連結するデスクトップアプリ。
仕様の正は `IDEA.txt`。決めていない項目は `IDEA.txt` 末尾。勝手に仕様を埋めない。
狙い: Windows 11 の `.exe`。スタックは FasTrim と同じく Python 3 + PySide6 + Pillow。
UI 文言は英語（CJK フォントが無い環境でも読めるようにする）。

## 決まっていること

- 複数画像を投入し、右へ連結する。並びはドロップ順、あとからサムネイルで並べ替え
- 高さは1枚目を基準に拡大縮小で揃える
- 連結結果の幅/高さは 16:9 を超えて横長にしない
- 超える場合の調整は、完成キャンバスを一括トリムするのではなく、**上限幅（高さ×16/9÷枚数）より広い画像だけを左右中央トリムする**
- 上限幅より細い画像はそのまま残す。細いことはエラーにしない
- 最初から 16:9 以下ならトリムしない（幅は揃えない）
- 1枚目がすでに 16:9 より横長ならエラー
- 隙間なし。保存は別名。元ファイルは上書きしない
- ウィンドウタイトルは `FasTitch`

## よく使うコマンド

リポジトリルート、venv 前提。

- Linux: `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt`
- Windows / Git Bash: `python -m venv .venv_win` → `source .venv_win/Scripts/activate` → `pip install -r requirements.txt`
- 起動: `python -m fastitch` または `./run.sh`
- テスト: `pip install pytest` のあと `python -m pytest`
- テスト単体: `python -m pytest tests/<file>.py::<test_name>`
- exe（Windows / Git Bash のみ）: `pip install pyinstaller` → `pyinstaller fastitch.spec`

Lint / 整形 / CI は作らない。cmd / PowerShell 向け手順は書かない。

## アーキテクチャ

ドメイン（連結・スケール・左右トリム・保存・命名）は Qt 非依存。UI がそれを呼ぶ。逆 import しない。

- ドメイン: `fastitch/geom.py`, `imageops.py`, `naming.py`, `config.py`, `constants.py`
- UI: `fastitch/app.py`, `preview.py`, `dialogs.py`, `theme.py`, `dnd.py`

選択・クロップの箱は PIL と同じ左上 inclusive・右下 exclusive `(l, t, r, b)`。

データ流: ファイル → `load_image`。サイズから `plan_stitch`。プレビューと保存は `render_stitch`。保存先は `naming.next_dest_path`。

## 実装するときのルール

- `pil_to_qpixmap` は `QImage.copy()` が必要
- HEIC は `pillow-heif` があれば有効。必須依存にしない
- `pytest` は `requirements.txt` に入れない。GUI テストは `QT_QPA_PLATFORM=offscreen` と設定ディレクトリの退避（`FASTITCH_CONFIG_DIR`）
- venv は OS 専用。Linux `.venv` / Windows `.venv_win`
- Windows 作業は Git Bash。activate は `source .venv_win/Scripts/activate`
- `.exe` は Windows でだけ固める
- ウィンドウタイトルは `FasTitch`
- アイコンは `assets/FasTitch.ico`（+ `assets/icon.png`）。タスクバーと exe は ico、実行時は `theme.asset_path` が PyInstaller の `_MEIPASS` も見る。デザイン変更時は `fastitch.theme.make_app_icon` の描画と揃える

## 注意

- `IDEA.txt` の「決まってないこと」を、確認なしに製品仕様へしない
- 設定は `%APPDATA%/FasTitch/settings.json`（Windows）または `~/.config/fastitch/settings.json`。退避先は環境変数 `FASTITCH_CONFIG_DIR`。`tests/conftest.py` がテスト中に一時ディレクトリへ向ける
- 同 conftest が `QT_QPA_PLATFORM=offscreen` をセットする
- `dist/` `build/` `.venv/` `.venv_win/` は生成物。コミットしない。`assets/` はコミットする
- エージェント向け指示は `AGENTS.md` のみ。`CLAUDE.md` / `.cursorrules` / `.github/copilot-instructions.md` などは作らない
