#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if required packages are installed
if ! pip show flask > /dev/null 2>&1; then
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Start the Flask application
echo "Starting pyFormanceTester web application..."
python app.py
