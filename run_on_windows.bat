@echo off
if exist myenv (
    call myenv\Scripts\activate.bat
    python scripts\run.py
) else (
    python -m venv myenv
    call myenv\Scripts\activate.bat
    python -m pip install requests >NUL
    python scripts\run.py
)
