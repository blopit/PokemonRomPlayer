#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR if not already installed
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v tesseract &> /dev/null; then
        echo "Installing Tesseract OCR via Homebrew..."
        brew install tesseract
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if ! command -v tesseract &> /dev/null; then
        echo "Installing Tesseract OCR..."
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr
    fi
fi

echo "Setup complete! Activate the virtual environment with: source venv/bin/activate" 