#!/bin/bash
# Create virtual environment for the speech client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Virtual environment created and dependencies installed."
echo "Run 'source venv/bin/activate' to activate, then 'python pubsub.py' to start."
