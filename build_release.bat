@echo off
REM ========================================================
REM TREQSO Automation Tool v1.0.2 - Release Build Script
REM
REM Prerequisites (on this developer build machine only):
REM   - Python 3.10+
REM   - Node.js (for npm install and tsc)
REM   - node_portable\node.exe  (portable Windows binary from nodejs.org)
REM   - Inno Setup 6 (optional, for creating the installer .exe)
REM
REM End users do NOT need Node.js — it is bundled as node_portable\node.exe.
REM ========================================================

echo ================================================
echo TREQSO Automation Tool v1.0.2 - Release Build
echo ================================================
echo.

REM ========================================================
REM Step 1: Verify node_portable\node.exe is present
REM ========================================================
echo [1/8] Checking for portable Node.js...
echo.

if not exist "node_portable\node.exe" (
    echo ================================================
    echo ERROR: node_portable\node.exe not found!
    echo ================================================
    echo.
    echo This file is required to make the application fully portable.
    echo End users will not need to install Node.js because this file
    echo is bundled inside the installer.
    echo.
    echo How to obtain it:
    echo   1. Go to: https://nodejs.org/en/download
    echo   2. Under "Prebuilt Binaries", choose:
    echo        Platform  : Windows
    echo        Version   : LTS
    echo        OS        : x64
    echo        Package   : Binary ^(.zip^)
    echo   3. Extract the zip.
    echo   4. Copy node.exe from the root of the extracted folder to:
    echo        %CD%\node_portable\node.exe
    echo   5. Re-run this script.
    echo.
    pause
    exit /b 1
)

for %%A in ("node_portable\node.exe") do set NODE_SIZE=%%~zA
echo + node_portable\node.exe found ^(%NODE_SIZE% bytes^)
echo.

REM ========================================================
REM Step 2: Clean previous builds
REM ========================================================
echo [2/8] Cleaning previous builds...
if exist "dist\TREQSO_Automation.exe" del "dist\TREQSO_Automation.exe"
if exist "build"            rmdir /s /q "build"
if exist "installer_output" rmdir /s /q "installer_output"
echo + Cleanup complete
echo.

REM ========================================================
REM Step 3: Install / update Python dependencies
REM ========================================================
echo [3/8] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --break-system-packages 2>nul || python -m pip install -r requirements.txt
python -m pip install pyinstaller           --break-system-packages 2>nul || python -m pip install pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo X Failed to install Python dependencies
    pause
    exit /b 1
)
echo + Python dependencies installed
echo.

REM ========================================================
REM Step 4: Install / update Node.js dependencies
REM ========================================================
echo [4/8] Installing Node.js dependencies ^(developer machine only^)...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo X npm install failed
    pause
    exit /b 1
)
echo + Node.js dependencies installed
echo.

REM ========================================================
REM Step 5: Verify required data files
REM ========================================================
echo [5/8] Verifying required files...

if not exist ".env.template" (
    echo Creating .env.template...
    (
        echo # TREQSO Configuration
        echo TREQSO_URL=https://your-treqso-url.com
        echo COMPANY=YourCompany
        echo TREQSO_HEADLESS=false
        echo TREQSO_SLOW_MO=0
    ) > .env.template
)

if not exist "sample_parts.csv" (
    echo WARNING: sample_parts.csv not found
)
if not exist "sample_bom.csv" (
    echo WARNING: sample_bom.csv not found
)

echo + Required files verified
echo.

REM ========================================================
REM Step 6: Compile TypeScript
REM ========================================================
echo [6/8] Compiling TypeScript...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo X TypeScript compilation failed
    pause
    exit /b 1
)
echo + TypeScript compiled ^(dist\cli.js, dist\treqso-automation.js^)
echo.

REM ========================================================
REM Step 7: Build standalone Python executable with PyInstaller
REM ========================================================
echo [7/8] Building Python executable with PyInstaller...
echo ^(This may take a few minutes^)
echo.
python -m PyInstaller TREQSO_Automation.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo X PyInstaller failed
    pause
    exit /b 1
)

if not exist "dist\TREQSO_Automation.exe" (
    echo X Executable not produced — check output above
    pause
    exit /b 1
)
for %%A in ("dist\TREQSO_Automation.exe") do set EXE_SIZE=%%~zA
echo + Executable created: dist\TREQSO_Automation.exe ^(%EXE_SIZE% bytes^)
echo.

REM ========================================================
REM Step 8: Create Inno Setup installer
REM ========================================================
echo [8/8] Building installer...
where iscc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo + Inno Setup found — compiling installer...
    iscc installer_script.iss
    if %ERRORLEVEL% EQU 0 (
        echo + Installer created in installer_output\
    ) else (
        echo ! Installer compilation failed — executable is still usable
    )
) else (
    echo ! Inno Setup ^(iscc^) not found — skipping installer step
    echo   Download Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo   The standalone executable is still available in dist\
)
echo.

REM ========================================================
REM Build summary
REM ========================================================
echo ================================================
echo Build Complete!
echo ================================================
echo.
echo Outputs:
echo   Executable : dist\TREQSO_Automation.exe
if exist "installer_output\" (
    echo   Installer  : installer_output\TREQSO_Automation_Setup_v2.1.0.exe
)
echo.
echo The installer is fully self-contained:
echo   - No Node.js installation required on end-user machines
echo   - node_portable\node.exe is bundled inside the installer
echo   - node_modules are bundled inside the installer
echo   - Playwright Chromium browser is downloaded automatically on first launch
echo.
echo Next steps:
echo   1. Test the installer on a machine without Node.js installed
echo   2. Distribute installer_output\TREQSO_Automation_Setup_v2.1.0.exe
echo.
pause
