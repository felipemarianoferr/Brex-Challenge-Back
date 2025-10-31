#!/bin/bash
# Setup script for Linux/Mac

echo "Creating virtual environment..."
python3 -m venv venv

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Remember to:"
echo "1. Create a .env file with your OPENROUTER_API_KEY"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the analysis: python run_analysis.py"
echo ""

