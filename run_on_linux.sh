#!/bin/bash
if [ -d "venv_chv" ]; then
    source venv_chv/bin/activate
else
    python3 -m venv venv_chv
    source venv_chv/bin/activate
    python3 -m pip install requests >/dev/null
fi

# cleanup for old versions of 4chv
rm *.html
rm -rf "myenv"

python3 main/chv_run.py
