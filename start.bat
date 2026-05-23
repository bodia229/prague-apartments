@echo off
setlocal

:: Always run from the folder where start.bat lives
cd /d "%~dp0"

title Prague Apartment Monitor
color 0A

echo.
echo  ============================================================
echo   Prague Apartment Monitor  ^|  Setup ^& Start
echo  ============================================================
echo.

:: ── 0. Kill any existing bot instance ───────────────────────
wmic process where "name='python.exe' and commandline like '%%tg_bot%%'" get processid 2>nul | findstr /r "[0-9]" >nul
if not errorlevel 1 (
    echo  Stopping previous bot instance...
    wmic process where "name='python.exe' and commandline like '%%tg_bot%%'" delete >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: ── 1. Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 goto :no_python

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   Python : %%v

:: ── 2. Check Python ^>= 3.10 ──────────────────────────────────
python -c "import sys; exit(0 if sys.version_info>=(3,10) else 1)" 2>nul
if errorlevel 1 goto :old_python

:: ── 3. Check config.py ───────────────────────────────────────
:: exit 0 = OK, 1 = token missing, 2 = chat id missing
python -c "from config import TG_BOT_TOKEN,TG_CHAT_ID; t=TG_BOT_TOKEN not in('YOUR_TOKEN_HERE','paste-your-token-here',''); c=str(TG_CHAT_ID) not in('0','123456789',''); exit(0 if t and c else (2 if t else 1))" 2>nul
if errorlevel 2 goto :no_chatid
if errorlevel 1 goto :no_token

echo   Config : OK

:: ── 4. Install dependencies ───────────────────────────────────
echo.
echo  Checking dependencies...
python -m pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 goto :pip_fail
echo   Deps   : OK

:: ── 5. Start bot ──────────────────────────────────────────────
echo.
echo  ============================================================
echo   Bot is running. Open Telegram and send /start to your bot.
echo   Press Ctrl+C or close this window to stop.
echo  ============================================================
echo.
python tg_bot.py

echo.
echo  Bot has stopped.
pause
exit /b 0


:: ── Error handlers ────────────────────────────────────────────

:no_python
echo  [ERROR] Python is not installed or not found in PATH.
echo.
echo  1. Download Python 3.10+ from https://www.python.org/downloads/
echo  2. During installation, check the box:
echo       "Add Python to PATH"
echo  3. Run start.bat again.
echo.
pause
exit /b 1

:old_python
echo  [ERROR] Python 3.10 or newer is required.
echo.
echo  Download the latest version from https://www.python.org/downloads/
pause
exit /b 1

:no_token
echo  [SETUP REQUIRED] TG_BOT_TOKEN is not set in config.py
echo.
echo  How to get a token:
echo    1. Open Telegram and search for @BotFather
echo    2. Send /newbot and follow the steps
echo    3. Copy the token BotFather gives you
echo    4. Open config.py and set:
echo         TG_BOT_TOKEN = "1234567890:AAHs_Jf82nMk..."
echo.
start notepad config.py
echo  config.py has been opened. Save it and run start.bat again.
echo.
pause
exit /b 1

:no_chatid
echo  [SETUP REQUIRED] TG_CHAT_ID is not set in config.py
echo.
echo  How to find your Chat ID:
echo    1. Send any message to your bot in Telegram
echo    2. Open this URL in your browser (replace TOKEN):
echo         https://api.telegram.org/botTOKEN/getUpdates
echo    3. Find "id" inside "chat" - that number is your Chat ID
echo    4. Open config.py and set:
echo         TG_CHAT_ID = 874093938
echo.
start notepad config.py
echo  config.py has been opened. Save it and run start.bat again.
echo.
pause
exit /b 1

:pip_fail
echo  [ERROR] Failed to install dependencies.
echo.
echo  Try running this command manually:
echo    pip install -r requirements.txt
echo.
pause
exit /b 1
