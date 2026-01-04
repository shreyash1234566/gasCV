@echo off
echo 🚀 Starting CO2Watch India Dashboard...
echo.

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo 🚀 Launching Streamlit App...
streamlit run app_new.py

pause
