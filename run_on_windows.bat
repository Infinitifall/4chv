@echo off
if exist venv_chv (
    call venv_chv\Scripts\activate.bat
) else (
    python -m venv venv_chv
    call venv_chv\Scripts\activate.bat
    python -m pip install requests >NUL
)

@REM cleanup for old versions of 4chv
del *.html
del /S /F "myenv"

python3 scripts\run.py
