# ============================================================================
# Fahr - Xodim Vaqti Hisoblash Boti
# Konfiguratsiya fayli
# ============================================================================

import os

# Telegram Bot Token
# Render'da "Environment" bo'limiga BOT_TOKEN qo'shing.
# Lokal kompyuterda ishlatish uchun pastdagi "YOUR_BOT_TOKEN_HERE" qiymatini o'zgartirishingiz mumkin.
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Boss (Admin) ning Telegram ID raqami
# Render'da "Environment" bo'limiga BOSS_ID qo'shing.
BOSS_ID = int(os.environ.get("BOSS_ID", "123456789"))

# Render bepul Web Service o'zining portini PORT environment variable orqali beradi
PORT = int(os.environ.get("PORT", "10000"))

# Database fayli nomi
DATABASE_FILE = "fahr_bot.db"

# Xodim vaqti kiritishda max soat (validation uchun)
MAX_HOURS_PER_DAY = 24

# Foydalanuvchi rollari
ROLE_BOSS = "boss"
ROLE_EMPLOYEE = "employee"

# Xodim statusi
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
