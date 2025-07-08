#!/bin/bash

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Virtual environment setup complete. Activate it using 'source .venv/bin/activate'."