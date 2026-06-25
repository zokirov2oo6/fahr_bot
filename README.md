# 🤖 Fahr - Xodim Vaqti Hisoblash Boti

Telegram botida Fahr korxonasi xodimlarining ish vaqtini hisoblash va boshqarish uchun dastur.

## 📋 Talablari

- Python 3.8+
- SQLite3 (kutubxona bilan birga o'rnatilgan)
- aiogram 3.x

## 🚀 O'rnatish va Ishga Tushirish

### 1. Loyihani Yuklab Olish
```bash
git clone <repository-url>
cd fahr-bot
```

### 2. Virtual Environment Yaratish
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac uchun
# yoki
venv\Scripts\activate  # Windows uchun
```

### 3. Kutubxonalarni O'rnatish
```bash
pip install -r requirements.txt
```

### 4. Konfiguratsiyani o'zgartirish
`config.py` faylini ochib, o'z ma'lumotlaringizni kiriting:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Botfather dan olingan tokenni qo'ying
BOSS_ID = 123456789  # O'z Telegram ID raqamingizni qo'ying
```

**Telegram ID raqamini qanday olish?**
1. `@userinfobot` botga xabar yuboring
2. U sizning ID raqamingizni beradi

**BOT_TOKEN qanday olish?**
1. `@BotFather` ga `/start` komandasini yuboring
2. `/newbot` buyrug'ini ishlatib yangi bot yarating
3. Bot nomini va username'sini kiriting
4. BotFather token beradi

### 5. Botni Ishga Tushirish
```bash
python main.py
```

## 📁 Fayllar Tuzilishi

```
fahr-bot/
├── config.py           # Konfiguratsiya (BOT_TOKEN, BOSS_ID)
├── database.py         # SQLite ma'lumotlar bazasi
├── main.py            # Bot asosiy logikasi va handlerlar
├── requirements.txt   # Kerakli kutubxonalar
└── fahr_bot.db        # SQLite database (avtomatik yaratiladi)
```

## 👥 Foydalanuvchi Rollari

### 1. **Boss (Admin)**
- Xodimlarni qabul qilish va tasdiqlash
- Xodimlarning soatbay haqini belgilash
- Barcha xodimlarning ish vaqtini ko'rish
- Vaqtni tahrirlash yoki yangi vaqt kiritish
- Umumiy oylik hisobotni ko'rish

### 2. **Xodim (Employee)**
- Bugungi ish vaqtini kiritish
- Kechagi ish vaqtini kiritish (unutilgan bo'lsa)
- O'z oylik hisob-kitobi va summasini ko'rish

## 🔄 Bot Ishlash Jarayoni

### Xodimning Ro'yxatdan O'tishi
1. Xodim `/start` komandasini yuborganda ism-familiyasini kiritadi
2. Bazaga "pending" statusida saqlanadi
3. Boss xabar oladi va soatbay haqni kiritib tasdiqlab beradi
4. Xodim status "active" bo'ladi va xodim menyusidan foydalana oladi

### Vaqt Kiritish
- **Bugungi vaqt**: Bugun necha soat ishlaganini kiriting
- **Kechagi vaqt**: Kechagi kunni unutgan bo'lsa, vaqt kiritish mumkin
- **UNIQUE Constraint**: Shu kun uchun vaqt faqat bir marta kiritish mumkin

### Oylik Hisob
- Vaqt oralig'ini kiritish: `10.06.2026-13.07.2026`
- Bot avtomatik barcha soatlarni, soatbay haqni ko'paytirib, summasini hisoblaydi

## 📊 Database Jadvallari

### `users`
| Ustun | Tur | Ma'lumot |
|-------|-----|---------|
| user_id | INTEGER | Telegram ID (Primary Key) |
| full_name | TEXT | Ism-familiyasi |
| role | TEXT | "boss" yoki "employee" |
| hourly_rate | REAL | Soatbay haq (so'm/soat) |
| status | TEXT | pending/active/inactive |
| created_at | TIMESTAMP | Yaratilgan vaqti |
| updated_at | TIMESTAMP | Yangilangan vaqti |

### `work_hours`
| Ustun | Tur | Ma'lumot |
|-------|-----|---------|
| id | INTEGER | Primary Key |
| user_id | INTEGER | Foydalanuvchi ID |
| work_date | DATE | Ish kunining sanasi |
| hours | REAL | Ishlangan soatlar |
| created_at | TIMESTAMP | Yaratilgan vaqti |
| updated_at | TIMESTAMP | Yangilangan vaqti |
| UNIQUE | | (user_id, work_date) |

## 🛠️ Kerakli Ma'lumotlar (Config)

```python
BOT_TOKEN = "5789......"          # BotFather dan olingan
BOSS_ID = 987654321               # O'z Telegram ID
DATABASE_FILE = "fahr_bot.db"    # Database fayli nomi
```

## 🔒 Xavfsizlik Tavsiyalari

1. **BOT_TOKEN ni qaytarib shartnomasing ma'lumot qilmang**
   - Token ishlatilgan bot o'chirilsin
   - Yangi token olinsin

2. **BOSS_ID to'g'ri bo'lsin**
   - Xato ID bilsa, boss menyusiga kirita olmaydi

3. **.env faylini ishlatish** (keyinchalik)
   - Sensitiv ma'lumotlarni .env da saqlash tavsiya etiladi

## 📝 Misollar

### Xodim Oralig'iga Vaqt Kiriting
```
10.06.2026-13.07.2026
```

### Soat Kiritish
```
8       (to'liq soat)
7.5     (yarim soat)
```

## ❓ Tez-Tez So'raladigan Savollar

### Agar xodim statusini o'zgartirmoqchi bo'lsam?
Database.py da `update_user_status()` funksiyasini ishlatishingiz mumkin.

### Agar bot ishlamasa?
1. BOT_TOKEN to'g'ri ekanini tekshiring
2. Internet ulanishi bor ekanini tekshiring
3. aiogram kutubxonasini qayta o'rnating:
   ```bash
   pip install --upgrade aiogram
   ```

### Database faylini qayta yaratish
Agar database buzilsa:
```python
import os
os.remove("fahr_bot.db")
# Botni qayta ishga tushiring
```

## 📞 Qo'shimcha Yordamm

Agar savollar bo'lsa, Telegram orqali murojaat qilishingiz mumkin.

---

**Versiya**: 1.0  
**Oxirgi yangilash**: 2026-06-25
