@echo off
REM Smart Python Launcher - Automatically finds Python installation
REM For TREQSO Automation Tool

echo ================================================
echo TREQSO Automation Tool - Smart Launcher
echo ================================================
echo.
echo Searching for Python installation...
echo.

REM Try different Python commands
set PYTHON_CMD=

REM Method 1: Try "python"
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :found
)

REM Method 2: Try "py" (Python Launcher)
py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :found
)

REM Method 3: Try "python3"
python3 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :found
)

REM Method 4: Try common installation paths
set "TEST_PATH=C:\Python311\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :found
)

set "TEST_PATH=C:\Python310\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :found
)

set "TEST_PATH=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :found
)

set "TEST_PATH=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :found
)

REM Method 5: Check Microsoft Store installation
set "TEST_PATH=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :found
)

REM If we get here, Python was not found
echo ================================================
echo ERROR: Python Not Found!
echo ================================================
echo.
echo Python does not appear to be installed or is not in PATH.
echo.
echo Please install Python:
echo   1. Go to: https://www.python.org/downloads/
echo   2. Download Python 3.10 or newer
echo   3. Run installer
echo   4. CHECK the box "Add Python to PATH"
echo   5. Complete installation
echo.
echo After installing Python, run this script again.
echo.
pause
exit /b 1

:found
echo Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM Show menu
:menu
echo ================================================
echo Choose interface:
echo   1. GUI (Graphical Interface)
echo   2. CLI (Command Line Help)
echo   3. Install Dependencies
echo   4. Exit
echo ================================================
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto gui
if "%choice%"=="2" goto cli
if "%choice%"=="3" goto install
if "%choice%"=="4" goto exit
goto invalid

:gui
echo.
echo Launching GUI...
echo.
REM Check if dependencies are installed
%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: tkinter not installed!
    echo This should come with Python. You may need to reinstall Python.
    echo.
    pause
    goto menu
)

%PYTHON_CMD% -c "import dotenv" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: python-dotenv not installed!
    echo Installing dependencies...
    %PYTHON_CMD% -m pip install python-dotenv
    echo.
)

%PYTHON_CMD% -c "from win32 import win32print" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: pywin32 not installed!
    echo Installing dependencies...
    %PYTHON_CMD% -m pip install pywin32
    echo.
)

%PYTHON_CMD% treqso_gui.py
goto end

:cli
echo.
echo ================================================
echo TREQSO CLI Mode
echo ================================================
echo.
echo Available commands:
echo   %PYTHON_CMD% treqso_processor.py parts ^<csv_file^>
echo   %PYTHON_CMD% treqso_processor.py bom ^<csv_file^>
echo   %PYTHON_CMD% treqso_processor.py replace ^<assembly^> ^<old_pn^> ^<new_pn^> [qty]
echo   %PYTHON_CMD% treqso_processor.py test
echo.
echo Examples:
echo   %PYTHON_CMD% treqso_processor.py parts sample_parts.csv
echo   %PYTHON_CMD% treqso_processor.py bom sample_bom.csv
echo   %PYTHON_CMD% treqso_processor.py replace PCB-001 RES-001 RES-002 4
echo   %PYTHON_CMD% treqso_processor.py test
echo.
pause
goto end

:install
echo.
echo Installing Python dependencies...
echo.
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install python-dotenv
call npm install pdf-to-printer
call npx playwright install
echo.
echo Dependencies installed!
echo.
pause
goto menu

:invalid
echo.
echo Invalid choice. Please enter 1, 2, 3, or 4.
echo.
pause
goto menu

:exit
echo.
echo Exiting...
goto end

:end
