#!/bin/bash
if [ -d "venv_chv" ]; then
    source venv_chv/bin/activate > /dev/null
else
    python3 -m venv venv_chv > /dev/null
    source venv_chv/bin/activate > /dev/null
    python3 -m pip install --upgrade pip > /dev/null
    python3 -m pip install -r ./requirements.txt > /dev/null
fi

python3 main/chv_run.py
