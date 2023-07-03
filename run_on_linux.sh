#!/bin/bash
if [ -d "myenv" ]; then
    echo "Found myenv folder."
    source myenv/bin/activate
    python3 scripts/run.py
else
    echo "myenv folder not found. Creating a new virtual environment."
    python3 -m venv myenv
    source myenv/bin/activate
    python3 -m pip install requests
    python3 scripts/run.py
fi
