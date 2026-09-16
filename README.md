# FasTitch

複数画像を横に連結し、高さを1枚目に揃え、結果が 16:9 より横長にならないよう各画像の左右をトリムするアプリ。Windows 11 向け。

仕様の正は `IDEA.txt`。

## 必要環境

- Python 3.10 以降
- Windows では Git Bash（Git for Windows）

venv は OS をまたげません。Linux 用は `.venv`、Windows 用は `.venv_win` です。

## インストール（Linux / macOS）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## インストール（Windows / Git Bash）

```bash
python -m venv .venv_win
source .venv_win/Scripts/activate
pip install -r requirements.txt
```

## 起動

venv を activate した状態で:

```bash
python -m fastitch
```

または `./run.sh`

画像ファイルのパスを引数に渡せます。

```bash
python -m fastitch a.jpg b.jpg c.jpg
```

## テスト

```bash
pip install pytest
python -m pytest
```

## exe 化（Windows / Git Bash）

Linux からは作れません。venv を activate した Git Bash で:

```bash
pip install pyinstaller
pyinstaller fastitch.spec
```

`dist/FasTitch.exe` ができます。
