@echo off
setlocal

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo pip is not installed. Installing pip...
    python -m ensurepip --upgrade >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo pip installation failed.
        pause
        exit /b 1
    )
)

REM Check if requirements.txt exists
IF NOT EXIST requirements.txt (
    echo requirements.txt not found!
    pause
    exit /b 1
)

REM Install required packages quietly, show errors only
echo Installing required packages...
pip install --upgrade pip >nul
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install required packages.
    pause
    exit /b 1
)

echo Device ready to start bot... starting now

REM Run the bot and display its output
python bot.py
IF %ERRORLEVEL% NEQ 0 (
    echo An error occurred while running the bot.
)
pause
