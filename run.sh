#!/bin/bash
# News Feed - setup and run (Mac / Linux)

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Starting News Feed..."
python3 main.py

# requirement is Python 3.10+. Then: Mac/Linux: ./run.sh
# Windows: double-click run.bat or run it in a terminal