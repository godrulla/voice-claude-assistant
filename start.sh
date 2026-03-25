#!/bin/bash

# Voice Claude Assistant Starter Script

echo "🎤 Voice Claude Assistant"
echo "========================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import anthropic" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check for .env file
if [ ! -f "config/.env" ]; then
    echo "⚠️  config/.env not found!"
    echo "Creating from example..."
    cp config/.env.example config/.env
    echo "Please edit config/.env and add your ANTHROPIC_API_KEY"
    echo "Press Enter when ready..."
    read
fi

# Start the assistant
echo "Starting Voice Assistant..."
python -m src.main