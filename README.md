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

## exe 化（Windows / Git Bash、uv を使う場合）

uv が無ければ先に入れます。

```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

venv は uv に作らせ、そこへ pyinstaller を入れます。`uv pip` は activate 不要です。

```bash
uv venv --python 3.12 .venv_win
uv pip install --python .venv_win -r requirements.txt
uv pip install --python .venv_win pyinstaller
.venv_win/Scripts/pyinstaller fastitch.spec
```

`dist/FasTitch.exe` ができます。`.venv_win` は上の pip 手順と共通です。作り直すときは `.venv_win` を消してから `uv venv` を実行してください。

起動やテストも uv 経由でできます。

```bash
uv run --python .venv_win python -m fastitch
uv pip install --python .venv_win pytest
uv run --python .venv_win python -m pytest
```
