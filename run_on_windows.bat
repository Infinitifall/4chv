@echo off
if exist venv_chv (
    call venv_chv\Scripts\activate.bat >NUL
) else (
    python3 -m venv venv_chv >NUL
    call venv_chv\Scripts\activate.bat >NUL
    python3 -m pip install --upgrade pip >NUL
    python3 -m pip install -r ./requirements.txt >NUL
)

python3 scripts\run.py
