@echo off
:: =========================================================================
:: Apple USB HotSpot Driver Installer
:: Automatically adds Apple USB & Apple Mobile Device Ethernet drivers
:: =========================================================================

echo Checking Administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This installer requires Administrator permissions.
    echo Please right-click this file and select "Run as administrator".
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0
set DRIVERS_DIR=%SCRIPT_DIR%..\drivers

if not exist "%DRIVERS_DIR%\appleusb\AppleUsb.inf" (
    set DRIVERS_DIR=%SCRIPT_DIR%drivers
)

echo [INFO] Installing Apple USB Driver...
pnputil /add-driver "%DRIVERS_DIR%\appleusb\AppleUsb.inf" /install
if %errorLevel% neq 0 (
    echo [WARNING] Apple USB Driver installation encountered an issue or was already installed.
) else (
    echo [OK] Apple USB Driver installed successfully.
)

echo.
echo [INFO] Installing Apple Mobile Device Ethernet Driver...
pnputil /add-driver "%DRIVERS_DIR%\netaapl64\netaapl64.Inf" /install
if %errorLevel% neq 0 (
    echo [WARNING] Apple Mobile Device Ethernet Driver encountered an issue or was already installed.
) else (
    echo [OK] Apple Mobile Device Ethernet Driver installed successfully.
)

echo.
echo =========================================================================
echo Driver installation complete!
echo Connect your Apple device and enable Personal Hotspot in Settings.
echo =========================================================================
pause
