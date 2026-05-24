# ── НАЛАШТУВАННЯ ПОШУКУ КВАРТИР ───────────────────────────
# Змінюй ці значення під свої потреби

# Telegram — секрети читаються з .env (див. .env.example)
import os
from pathlib import Path


def _load_env_file() -> None:
    env_path = Path(__file__).with_name(".env")
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID   = int(os.getenv("TG_CHAT_ID", "0"))

if not TG_BOT_TOKEN or not TG_CHAT_ID:
    raise RuntimeError(
        "TG_BOT_TOKEN / TG_CHAT_ID не задані. Створи файл .env "
        "(шаблон у .env.example) або задай змінні середовища."
    )

# Тип угоди: "rent" або "sale"
DEAL_TYPE = "rent"

# Ціна (CZK на місяць для оренди)
PRICE_MIN = 0
PRICE_MAX = 25000

# Кімнати (список: "1+kk", "1+1", "2+kk", "2+1", "3+kk", "3+1", "4+kk", "4+1")
ROOMS = ["2+kk", "2+1", "3+kk", "3+1"]

# Площа (м²)
AREA_MIN = 40
AREA_MAX = 120

# Райони Праги (список: "Praha 1" ... "Praha 10", або [] для всіх)
DISTRICTS = []  # [] = всі райони

# Відстань до метро (метри, 0 = не перевіряти)
MAX_METRO_DISTANCE = 800  # 800м = ~10 хвилин пішки

# Додаткові фільтри (True/False/None — None = не важливо)
FURNISHED    = None   # меблі
PETS_ALLOWED = None   # тварини
BALCONY      = None   # балкон/тераса
PARKING      = None   # паркінг
ELEVATOR     = None   # ліфт

# Як часто перевіряти нові оголошення (секунди)
CHECK_INTERVAL = 1800  # 1800 = кожні 30 хвилин

# Які джерела включити
SOURCES = {
    "sreality":    True,
    "bezrealitky": True,
    "idnes":       True,
    "reality":     True,
    "facebook":    False,  # потребує Playwright + FB акаунт
}
