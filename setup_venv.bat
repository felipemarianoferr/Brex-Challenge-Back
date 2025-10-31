@echo off
REM Setup script for Windows
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo Remember to:
echo 1. Create a .env file with your OPENROUTER_API_KEY
echo 2. Activate the virtual environment: venv\Scripts\activate
echo 3. Run the analysis: python run_analysis.py
echo.

