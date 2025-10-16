#!/bin/bash

# ---------- Step 1: Navigate to project folder ----------
echo "Setting up virtual environment in $(pwd)..."

# ---------- Step 2: Create virtual environment ----------
python3 -m venv venv
echo "Virtual environment 'venv' created."

# ---------- Step 3: Activate virtual environment ----------
source venv/bin/activate
echo "Virtual environment activated."

# ---------- Step 4: Upgrade pip ----------
pip install --upgrade pip
echo "pip upgraded."

# ---------- Step 5: Install dependencies ----------
pip install flask flask-login pandas sqlalchemy plotly werkzeug
echo "Dependencies installed."

# ---------- Step 6: Done ----------
echo "Setup complete. To activate the environment in the future, run: source venv/bin/activate"