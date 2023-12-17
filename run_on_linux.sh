#!/bin/bash
if [ -d "myenv" ]; then
    source myenv/bin/activate
    python3 scripts/run.py
else
    python3 -m venv myenv
    source myenv/bin/activate
    python3 -m pip install requests >/dev/null
    python3 scripts/run.py
fi
