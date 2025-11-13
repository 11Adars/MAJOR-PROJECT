#!/bin/bash

echo "========================================"
echo "  Sign Language Recognition Service"
echo "  BankAssist AI - Customer Support"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found. Creating..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
    echo "[SUCCESS] Virtual environment created"
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    exit 1
fi

# Check if requirements are installed
echo "[INFO] Checking dependencies..."
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies"
        exit 1
    fi
    echo "[SUCCESS] Dependencies installed"
else
    echo "[SUCCESS] Dependencies already installed"
fi

# Check if model files exist
echo "[INFO] Checking model files..."
if [ ! -f "saved_model_landmarks/best_landmark_model.keras" ]; then
    echo "[WARNING] Sign recognition model not found!"
    echo "[WARNING] Expected: saved_model_landmarks/best_landmark_model.keras"
    echo "[WARNING] The service may not work properly without the model"
    echo ""
    read -p "Press Enter to continue..."
fi

if [ ! -f "processed_data_landmarks/sign_labels.npy" ]; then
    echo "[WARNING] Sign labels not found!"
    echo "[WARNING] Expected: processed_data_landmarks/sign_labels.npy"
    echo "[WARNING] The service may not work properly without labels"
    echo ""
    read -p "Press Enter to continue..."
fi

echo ""
echo "========================================"
echo "  Starting Sign Language Service"
echo "  URL: http://127.0.0.1:8000"
echo "========================================"
echo ""
echo "[INFO] Press Ctrl+C to stop the service"
echo ""

# Start the Flask service
python sign_service.py

# Deactivate virtual environment on exit
deactivate
