@echo off
if exist myenv (
    echo Found myenv folder.
    call myenv\Scripts\activate.bat
    cls
    python scripts\run.py
    pause
) else (
    echo myenv folder not found. Creating a new virtual environment.
    python -m venv myenv
    call myenv\Scripts\activate.bat
    python -m pip install requests
    cls
    python scripts\run.py
    pause
)
