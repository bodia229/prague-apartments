# ── НАЛАШТУВАННЯ ПОШУКУ КВАРТИР ───────────────────────────
# Змінюй ці значення під свої потреби

# Telegram
TG_BOT_TOKEN = "8905140234:AAF823MULxfJzO3zCtf_4psFspfgZ6soVJo"
TG_CHAT_ID   = 874093938

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
