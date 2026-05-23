#!/usr/bin/env bash
# Prague Apartment Monitor — Setup & Start
# Works on Linux and macOS

set -e

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}  ============================================================"
echo -e "   Prague Apartment Monitor  |  Setup & Start"
echo -e "  ============================================================${NC}"
echo ""

# ── 1. Find Python ────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo -e "  ${RED}[ERROR]${NC} Python is not installed."
    echo ""
    echo "  Install Python 3.10+:"
    echo "    macOS (Homebrew) : brew install python3"
    echo "    Ubuntu/Debian    : sudo apt install python3 python3-pip"
    echo "    Fedora/RHEL      : sudo dnf install python3"
    echo ""
    exit 1
fi

PY_VER=$($PY --version 2>&1)
echo -e "   Python : ${GREEN}${PY_VER}${NC}"

# ── 2. Verify version >= 3.10 ─────────────────────────────────
$PY -c "
import sys
if sys.version_info < (3, 10):
    print(f'Need Python 3.10+, found {sys.version}')
    exit(1)
" || {
    echo ""
    echo -e "  ${RED}[ERROR]${NC} Python 3.10 or newer is required."
    echo "  Update Python from https://www.python.org/downloads/"
    exit 1
}

# ── 3. Check config.py ────────────────────────────────────────
CFG_STATUS=$($PY -c "
from config import TG_BOT_TOKEN, TG_CHAT_ID
bad_token = TG_BOT_TOKEN in ('YOUR_TOKEN_HERE', 'paste-your-token-here', '')
bad_chat  = str(TG_CHAT_ID) in ('0', '123456789', '')
if bad_token:
    print('TOKEN_MISSING')
elif bad_chat:
    print('CHATID_MISSING')
else:
    print('OK')
" 2>/dev/null || echo "IMPORT_ERROR")

if [ "$CFG_STATUS" = "TOKEN_MISSING" ]; then
    echo ""
    echo -e "  ${YELLOW}[SETUP REQUIRED]${NC} TG_BOT_TOKEN is not set in config.py"
    echo ""
    echo "  Steps:"
    echo "    1. Open Telegram, search for @BotFather"
    echo "    2. Send /newbot and follow the instructions"
    echo "    3. Copy the token BotFather sends you"
    echo "    4. Edit config.py:"
    echo '         TG_BOT_TOKEN = "1234567890:ABCdef..."'
    echo ""
    echo "  Then run this script again."
    exit 1
fi

if [ "$CFG_STATUS" = "CHATID_MISSING" ]; then
    echo ""
    echo -e "  ${YELLOW}[SETUP REQUIRED]${NC} TG_CHAT_ID is not set in config.py"
    echo ""
    echo "  Steps:"
    echo "    1. Send any message to your bot in Telegram"
    echo "    2. Open in browser (replace TOKEN with yours):"
    echo "         https://api.telegram.org/botTOKEN/getUpdates"
    echo '    3. Find "id" inside "chat" — that is your Chat ID'
    echo "    4. Edit config.py:"
    echo "         TG_CHAT_ID = 123456789"
    echo ""
    echo "  Then run this script again."
    exit 1
fi

if [ "$CFG_STATUS" = "IMPORT_ERROR" ]; then
    echo ""
    echo -e "  ${RED}[ERROR]${NC} Could not read config.py. Is it in the same folder?"
    exit 1
fi

echo -e "   Config : ${GREEN}OK${NC}"

# ── 4. Install / update dependencies ─────────────────────────
echo ""
echo "  Checking dependencies..."
$PY -m pip install -r requirements.txt --quiet --disable-pip-version-check 2>&1 | grep -v "^$" || true
echo -e "   Deps   : ${GREEN}OK${NC}"

# ── 5. Start ─────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  ============================================================"
echo -e "   Bot is starting. Open Telegram and send /start to your bot."
echo -e "   Press Ctrl+C to stop the bot."
echo -e "  ============================================================${NC}"
echo ""

$PY tg_bot.py
