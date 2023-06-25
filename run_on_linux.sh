#!/bin/bash
if [ -d "myenv" ]; then
    echo "Found myenv folder."
    source myenv/bin/activate
    python scripts/run.py
else
    echo "myenv folder not found. Creating a new virtual environment."
    python3 -m venv myenv
    source myenv/bin/activate
    python -m pip install requests
    python scripts/run.py
fi
