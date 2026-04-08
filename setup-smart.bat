@echo off
REM Smart Setup Script - TREQSO Automation Tool v2.1
REM
REM FOR DEVELOPERS only — sets up the project for local development and building.
REM
REM End users should run the installer (TREQSO_Automation_Setup_v2.1.0.exe) instead.
REM Node.js is bundled inside the installer and is NOT required on end-user machines.
REM
REM Developer prerequisites:
REM   - Python 3.10+  (https://www.python.org/)
REM   - Node.js LTS   (https://nodejs.org/)          <- dev/build only
REM   - node_portable\node.exe                        <- for build_release.bat

echo ================================================
echo TREQSO Automation v2.1 - Developer Setup
echo ================================================
echo.

REM ============================================
REM Step 1: Find Python
REM ============================================
echo [1/4] Searching for Python...
echo.

set PYTHON_CMD=

REM Try different Python commands
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :python_found
)

py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py
    goto :python_found
)

python3 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :python_found
)

REM Try common installation paths
set "TEST_PATH=C:\Python311\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :python_found
)

set "TEST_PATH=C:\Python310\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :python_found
)

set "TEST_PATH=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :python_found
)

set "TEST_PATH=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if exist "%TEST_PATH%" (
    set PYTHON_CMD=%TEST_PATH%
    goto :python_found
)

REM Python not found
echo X Python not found!
echo.
echo Please install Python:
echo   1. Visit: https://www.python.org/downloads/
echo   2. Download Python 3.10 or newer
echo   3. Run installer and CHECK "Add Python to PATH"
echo   4. Run this script again
echo.
pause
exit /b 1

:python_found
echo + Python found: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM ============================================
REM Step 2: Check Node.js
REM ============================================
echo [2/4] Checking Node.js...
echo.

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Node.js not found!
    echo.
    echo Please install Node.js:
    echo   1. Visit: https://nodejs.org/
    echo   2. Download LTS version
    echo   3. Install and restart this script
    echo.
    pause
    exit /b 1
)

node --version
echo + Node.js found
echo.

REM ============================================
REM Step 3: Install Node.js dependencies
REM ============================================
echo [3/4] Installing Node.js dependencies...
echo.

call npm install
if %ERRORLEVEL% NEQ 0 (
    echo X npm install failed
    pause
    exit /b 1
)
echo + Node.js dependencies installed
echo.

echo Installing Playwright browsers...
call npx playwright install
if %ERRORLEVEL% NEQ 0 (
    echo X Playwright browser installation failed
    pause
    exit /b 1
)
echo + Playwright browsers installed
echo.

REM ============================================
REM Step 4: Install Python dependencies
REM ============================================
echo [4/4] Installing Python dependencies...
echo.

%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install python-dotenv
%PYTHON_CMD% -m pip install pywin32

if %ERRORLEVEL% NEQ 0 (
    echo X Python pip install failed
    pause
    exit /b 1
)
echo + Python dependencies installed
echo.

REM ============================================
REM Step 5: Build TypeScript
REM ============================================
echo Building TypeScript code...
echo.

call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo X TypeScript build failed
    pause
    exit /b 1
)
echo + TypeScript compiled successfully
echo.

REM ============================================
REM Step 6: Create .env file
REM ============================================
echo Creating .env file...
echo.

if not exist .env (
    copy .env.template .env
    echo + .env file created - PLEASE EDIT IT WITH YOUR CREDENTIALS
) else (
    echo i .env file already exists, skipping...
)
echo.

REM ============================================
REM Complete!
REM ============================================
echo ================================================
echo + Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env file with your TREQSO credentials
echo 2. Find TREQSO selectors:
echo    npx playwright codegen https://your-treqso.com
echo 3. Update src/treqso-automation.ts with selectors
echo 4. Rebuild: npm run build
echo 5. Launch: launcher-smart.bat
echo.
echo Your Python command is: %PYTHON_CMD%
echo   Use this in any manual commands you run
echo.
echo See GUIDE.md for detailed instructions
echo.
pause
