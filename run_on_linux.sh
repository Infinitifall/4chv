#!/bin/bash
if [ -d "myenv" ]; then
    source myenv/bin/activate
else
    python3 -m venv myenv
    source myenv/bin/activate
    python3 -m pip install requests >/dev/null
fi

python3 scripts/chv_run.py
