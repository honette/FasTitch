# FasJoin

複数画像を横に連結し、高さを1枚目に揃え、結果が 16:9 より横長にならないよう各画像の左右をトリムするアプリ。Windows 11 向け。

**まだ未実装。** 仕様の正は `IDEA.txt`。このフォルダごと別リポジトリに移して実装する想定。

## 実装時の環境（予定）

FasTrim と同じ。

- Python 3.10 以降 + PySide6 + Pillow
- UI 文言は英語
- Linux 用 venv は `.venv`、Windows 用は `.venv_win`（混ぜない）
- Windows のコマンドは Git Bash 前提
  `python -m venv .venv_win` → `source .venv_win/Scripts/activate`
- `.exe` は Windows 上の PyInstaller のみ（Linux からクロスコンパイルしない）

コードが入ったら、ここにインストールと起動手順を書く。
