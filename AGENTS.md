# AGENTS.md

このファイルは、このリポジトリで作業するAIコーディングエージェントへの指示です。

## プロジェクト概要

FasJoin は複数画像を右方向へ連結するデスクトップアプリ。未実装。
仕様の正は `IDEA.txt`。決めていない項目は `IDEA.txt` 末尾。勝手に仕様を埋めない。
狙い: Windows 11 の `.exe`。スタックは FasTrim と同じく Python 3 + PySide6 + Pillow。
UI 文言は英語（CJK フォントが無い環境でも読めるようにする）。

## 決まっていること

- 複数画像を投入し、右へ連結する
- 高さは1枚目を基準に揃える
- 連結結果の幅/高さは 16:9 を超えて横長にしない
- 超える場合の調整は、完成キャンバスを一括トリムするのではなく、**各画像の左右を切って細くする**
- 保存は別名。元ファイルは上書きしない

## よく使うコマンド

コードが無いので、実装後にこの節を実コマンドへ更新する。
実装時の型:

- Linux: `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt`
- Windows / Git Bash: `python -m venv .venv_win` → `source .venv_win/Scripts/activate` → `pip install -r requirements.txt`
- 起動: `python -m fasjoin` または `./run.sh`
- テスト: `pip install pytest` のあと `python -m pytest`
- テスト単体: `python -m pytest tests/<file>.py::<test_name>`
- exe（Windows / Git Bash のみ）: `pip install pyinstaller` → `pyinstaller fasjoin.spec`

Lint / 整形 / CI は作らない。cmd / PowerShell 向け手順は書かない。

## 実装するときのルール

- ドメイン（連結・スケール・左右トリム・保存）は Qt 非依存。UI がそれを呼ぶ。逆 import しない
- 選択・クロップの箱は PIL と同じ左上 inclusive・右下 exclusive `(l, t, r, b)`
- `pil_to_qpixmap` は `QImage.copy()` が必要
- HEIC は `pillow-heif` があれば有効。必須依存にしない
- `pytest` は `requirements.txt` に入れない。GUI テストは `QT_QPA_PLATFORM=offscreen` と設定ディレクトリの退避（例: `FASJOIN_CONFIG_DIR`）
- venv は OS 専用。Linux `.venv` / Windows `.venv_win`
- Windows 作業は Git Bash。activate は `source .venv_win/Scripts/activate`
- `.exe` は Windows でだけ固める
- ウィンドウタイトルは `FasJoin`

## 注意

- `IDEA.txt` の「決まってないこと」を、確認なしに製品仕様へしない
- `dist/` `build/` `.venv/` `.venv_win/` は生成物。コミットしない
- エージェント向け指示は `AGENTS.md` のみ。`CLAUDE.md` / `.cursorrules` / `.github/copilot-instructions.md` などは作らない
