# ============================================================================
# Fahr - Xodim Vaqti Hisoblash Boti
# Asosiy Bot Logikasi va Handlerlar
# ============================================================================

import asyncio
from datetime import datetime, date, timedelta
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from config import BOT_TOKEN, BOSS_ID, ROLE_BOSS, ROLE_EMPLOYEE, STATUS_ACTIVE, STATUS_PENDING
from database import db, Database


# ===================== FSM HOLATLAR =====================

class EmployeeRegistration(StatesGroup):
    """Yangi xodim ro'yxatdan o'tish holatlari"""
    waiting_for_name = State()


class EmployeeMenu(StatesGroup):
    """Xodim menyusi holatlari"""
    main = State()
    waiting_hours_today = State()
    waiting_hours_yesterday = State()
    waiting_date_range = State()


class BossMenu(StatesGroup):
    """Boss menyusi holatlari"""
    main = State()
    waiting_hourly_rate = State()
    choosing_employee_for_edit = State()
    waiting_edit_date = State()
    waiting_edit_hours = State()
    waiting_report_date_range = State()


# ===================== BOT INITSIALIZATSIYASI =====================

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ===================== YORDAMCHI FUNKSIYALAR =====================

def is_boss(user_id: int) -> bool:
    """User Boss ekanini tekshirish"""
    return user_id == BOSS_ID


async def send_boss_notification(message_text: str, reply_markup: Optional[InlineKeyboardMarkup] = None):
    """Bossga xabar yuborish"""
    try:
        await bot.send_message(BOSS_ID, message_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        print(f"Bosshga xabar yuborishda xato: {e}")


def get_boss_menu() -> ReplyKeyboardMarkup:
    """Boss uchun asosiy menyuni yaratish"""
    keyboard = [
        [KeyboardButton(text="📊 Xodimlar vaqtini ko'rish")],
        [KeyboardButton(text="✏️ Vaqt tahrirlash / Kiritish")],
        [KeyboardButton(text="💰 Umumiy Hisobot (Summa)")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_employee_menu() -> ReplyKeyboardMarkup:
    """Xodim uchun asosiy menyuni yaratish"""
    keyboard = [
        [KeyboardButton(text="🕒 Bugungi vaqtni kiritish")],
        [KeyboardButton(text="📅 Kechagi vaqtni kiritish")],
        [KeyboardButton(text="💵 Mening oyligim (Summa)")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)


def parse_date_range(date_range_str: str) -> Optional[tuple]:
    """Vaqt oralig'ini parsing qilish (DD.MM.YYYY-DD.MM.YYYY)"""
    try:
        parts = date_range_str.strip().split('-')
        if len(parts) != 2:
            return None
        
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        
        start_date = datetime.strptime(start_str, "%d.%m.%Y").date()
        end_date = datetime.strptime(end_str, "%d.%m.%Y").date()
        
        if start_date > end_date:
            return None
        
        return (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    except:
        return None


def format_date(date_str: str) -> str:
    """Sanani formatlash (YYYY-MM-DD -> DD.MM.YYYY)"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except:
        return date_str


def is_valid_hours(hours_str: str) -> bool:
    """Soat raqami to'g'ri ekanini tekshirish"""
    try:
        hours = float(hours_str)
        return 0 < hours <= 24
    except:
        return False


def get_yesterday_date() -> str:
    """Kechagi sanani olish (YYYY-MM-DD formatida)"""
    yesterday = date.today() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def get_today_date() -> str:
    """Bugungi sanani olish (YYYY-MM-DD formatida)"""
    return date.today().strftime("%Y-%m-%d")


# ===================== /START KOMANDASI =====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Bot boshlanish komandasI"""
    user_id = message.from_user.id
    
    # User bazada mavjudmi tekshirish
    user = db.get_user(user_id)
    
    if user is None:
        # Yangi user
        if is_boss(user_id):
            # Boss
            boss_user = db.add_user(user_id, "Boss", role=ROLE_BOSS, status=STATUS_ACTIVE)
            await message.answer(
                "👋 Salom, Boss! Xush kelibsiz.\n\n"
                "Siz xodimlarning ish vaqtini boshqarasiz.",
                reply_markup=get_boss_menu()
            )
            await state.set_state(BossMenu.main)
        else:
            # Yangi xodim
            await message.answer(
                "👋 Salom! Fahr xodim vaqti hisoblash botiga xush kelibsiz.\n\n"
                "Iltimos, to'liq ism-familiyangizni kiriting:"
            )
            await state.set_state(EmployeeRegistration.waiting_for_name)
    else:
        # Mavjud user
        if user['role'] == ROLE_BOSS:
            await message.answer("👋 Salom, Boss! Xush kelibsiz.", reply_markup=get_boss_menu())
            await state.set_state(BossMenu.main)
        else:
            if user['status'] == STATUS_PENDING:
                await message.answer(
                    "⏳ Sizning arizangiz hali Bossh tasdiqlanmagan.\n"
                    "Iltimos, Bosshning tasdiqini kutib turing."
                )
            elif user['status'] == STATUS_ACTIVE:
                await message.answer(
                    f"👋 Salom, {user['full_name']}! Xush kelibsiz.\n\n"
                    f"Soatbay haqqingiz: {user['hourly_rate']} so'm/soat",
                    reply_markup=get_employee_menu()
                )
                await state.set_state(EmployeeMenu.main)


# ===================== XODIM RO'YXATDAN O'TISHI =====================

@dp.message(EmployeeRegistration.waiting_for_name)
async def employee_register_name(message: types.Message, state: FSMContext):
    """Xodim ismini qabul qilish"""
    full_name = message.text.strip()
    
    if len(full_name) < 3:
        await message.answer("❌ Iltimos, to'g'ri ism-familiyangizni kiriting (minimal 3 ta belgi).")
        return
    
    user_id = message.from_user.id
    
    # Xodimni bazaga qo'shish
    if db.add_user(user_id, full_name, role=ROLE_EMPLOYEE, status=STATUS_PENDING):
        await message.answer(
            f"✅ Rahmat, {full_name}!\n\n"
            f"Sizning arizangiz Bosshga yuborildi. "
            f"Iltimos, tasdiqni kutib uring."
        )
        
        # Bossga xabar yuborish
        inline_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve_employee:{user_id}"
                )
            ]
        ])
        
        await send_boss_notification(
            f"📋 <b>Yangi Xodim Ariza</b>\n\n"
            f"<b>Ism-familiyasi:</b> {full_name}\n"
            f"<b>Telegram ID:</b> {user_id}\n\n"
            f"Xodim uchun soatbay haqni kiriting va tasdiqing.",
            reply_markup=inline_buttons
        )
        
        await state.clear()
    else:
        await message.answer("❌ Xatoli. Iltimos, qayta urinib ko'ring.")


# ===================== BOSS: XODIM TASDIQISH =====================

@dp.callback_query(F.data.startswith("approve_employee:"))
async def boss_approve_employee(callback: types.CallbackQuery, state: FSMContext):
    """Xodimni tasdiqish uchun soatbay haq so'rash"""
    user_id_to_approve = int(callback.data.split(":")[1])
    
    # State'ga ma'lumot saqlash
    await state.update_data(employee_to_approve=user_id_to_approve)
    await state.set_state(BossMenu.waiting_hourly_rate)
    
    user = db.get_user(user_id_to_approve)
    await callback.message.edit_text(
        f"💰 <b>{user['full_name']} uchun soatbay haqni kiriting</b>\n\n"
        f"Masalan: 10000 (so'm/soat)"
    )


@dp.message(BossMenu.waiting_hourly_rate)
async def boss_set_hourly_rate(message: types.Message, state: FSMContext):
    """Soatbay haqni qabul qilish va tasdiqish"""
    try:
        hourly_rate = float(message.text.strip())
        
        if hourly_rate <= 0:
            await message.answer("❌ Soatbay haq musbat son bo'lishi kerak.")
            return
        
        data = await state.get_data()
        employee_id = data['employee_to_approve']
        
        # Xodimni tasdiqish
        db.update_hourly_rate(employee_id, hourly_rate)
        db.update_user_status(employee_id, STATUS_ACTIVE)
        
        employee = db.get_user(employee_id)
        
        # Bossga tasdiq
        await message.answer(
            f"✅ Xodim Tasdiqlandi!\n\n"
            f"<b>Xodim:</b> {employee['full_name']}\n"
            f"<b>Soatbay haq:</b> {hourly_rate} so'm/soat",
            parse_mode="HTML",
            reply_markup=get_boss_menu()
        )
        
        # Xodimga xabar yuborish
        try:
            await bot.send_message(
                employee_id,
                f"✅ <b>Sizning arizangiz Tasdiqlandi!</b>\n\n"
                f"<b>Soatbay haqqingiz:</b> {hourly_rate} so'm/soat\n\n"
                f"Endi ish vaqtini kiritishni boshlashingiz mumkin.",
                parse_mode="HTML",
                reply_markup=get_employee_menu()
            )
        except Exception as e:
            print(f"Xodimga xabar yuborishda xato: {e}")
        
        await state.set_state(BossMenu.main)
    
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting (masalan: 10000).")


# ===================== XODIM: BUGUNGI VAQT =====================

@dp.message(EmployeeMenu.main, F.text == "🕒 Bugungi vaqtni kiritish")
async def employee_enter_today_hours(message: types.Message, state: FSMContext):
    """Bugungi vaqt kiritish boslanishi"""
    await message.answer(
        "🕒 <b>Bugungi Vaqt</b>\n\n"
        "Bugun necha soat ishladingiz? (Masalan: 8 yoki 7.5)",
        parse_mode="HTML"
    )
    await state.set_state(EmployeeMenu.waiting_hours_today)


@dp.message(EmployeeMenu.waiting_hours_today)
async def employee_save_today_hours(message: types.Message, state: FSMContext):
    """Bugungi vaqtni saqlash"""
    hours_text = message.text.strip()
    
    if not is_valid_hours(hours_text):
        await message.answer("❌ Iltimos, to'g'ri raqam kiriting (0-24 orasida).")
        return
    
    hours = float(hours_text)
    user_id = message.from_user.id
    today = get_today_date()
    
    success, result_message = db.add_work_hours(user_id, today, hours)
    
    if success:
        await message.answer(
            f"✅ {result_message}\n\n"
            f"<b>Sana:</b> {format_date(today)}\n"
            f"<b>Soat:</b> {hours} soat",
            parse_mode="HTML",
            reply_markup=get_employee_menu()
        )
    else:
        await message.answer(
            f"❌ {result_message}",
            reply_markup=get_employee_menu()
        )
    
    await state.set_state(EmployeeMenu.main)


# ===================== XODIM: KECHAGI VAQT =====================

@dp.message(EmployeeMenu.main, F.text == "📅 Kechagi vaqtni kiritish")
async def employee_enter_yesterday_hours(message: types.Message, state: FSMContext):
    """Kechagi vaqt kiritish boslanishi"""
    yesterday = get_yesterday_date()
    
    await message.answer(
        f"📅 <b>Kechagi Vaqt</b>\n\n"
        f"Sana: {format_date(yesterday)}\n"
        f"Necha soat ishladingiz? (Masalan: 8 yoki 7.5)",
        parse_mode="HTML"
    )
    await state.set_state(EmployeeMenu.waiting_hours_yesterday)


@dp.message(EmployeeMenu.waiting_hours_yesterday)
async def employee_save_yesterday_hours(message: types.Message, state: FSMContext):
    """Kechagi vaqtni saqlash"""
    hours_text = message.text.strip()
    
    if not is_valid_hours(hours_text):
        await message.answer("❌ Iltimos, to'g'ri raqam kiriting (0-24 orasida).")
        return
    
    hours = float(hours_text)
    user_id = message.from_user.id
    yesterday = get_yesterday_date()
    
    success, result_message = db.add_work_hours(user_id, yesterday, hours)
    
    if success:
        await message.answer(
            f"✅ {result_message}\n\n"
            f"<b>Sana:</b> {format_date(yesterday)}\n"
            f"<b>Soat:</b> {hours} soat",
            parse_mode="HTML",
            reply_markup=get_employee_menu()
        )
    else:
        await message.answer(
            f"❌ {result_message}",
            reply_markup=get_employee_menu()
        )
    
    await state.set_state(EmployeeMenu.main)


# ===================== XODIM: OYLIK HISOBOT =====================

@dp.message(EmployeeMenu.main, F.text == "💵 Mening oyligim (Summa)")
async def employee_request_salary_report(message: types.Message, state: FSMContext):
    """Oylik hisoboti uchun vaqt oralig'i so'rash"""
    await message.answer(
        "💵 <b>Oylik Hisobot</b>\n\n"
        "Sana oralig'ini kiriting (Format: DD.MM.YYYY-DD.MM.YYYY)\n\n"
        "Masalan: 10.06.2026-13.07.2026",
        parse_mode="HTML"
    )
    await state.set_state(EmployeeMenu.waiting_date_range)


@dp.message(EmployeeMenu.waiting_date_range)
async def employee_generate_salary_report(message: types.Message, state: FSMContext):
    """Oylik hisob-kitobi yaratish"""
    date_range = parse_date_range(message.text)
    
    if not date_range:
        await message.answer(
            "❌ Xato format.\n\n"
            "Iltimos, DD.MM.YYYY-DD.MM.YYYY formatida kiriting.\n"
            "Masalan: 10.06.2026-13.07.2026"
        )
        return
    
    start_date, end_date = date_range
    user_id = message.from_user.id
    
    # Ish soatlarini olish
    work_records = db.get_work_hours_range(user_id, start_date, end_date)
    user = db.get_user(user_id)
    
    if not work_records:
        await message.answer(
            f"📭 Bu oraliqda hech qanday ish soati kiritilmagan.\n\n"
            f"<b>Oralig'i:</b> {format_date(start_date)} - {format_date(end_date)}",
            parse_mode="HTML",
            reply_markup=get_employee_menu()
        )
        await state.set_state(EmployeeMenu.main)
        return
    
    # Hisob-kitobni hisoblash
    total_hours = sum(record['hours'] for record in work_records)
    total_salary = total_hours * user['hourly_rate']
    
    # Hisobotni formatlash
    report = f"""
📊 <b>Oylik Hisobot</b>

<b>Xodim:</b> {user['full_name']}
<b>Oralig'i:</b> {format_date(start_date)} - {format_date(end_date)}
<b>Soatbay haq:</b> {user['hourly_rate']} so'm/soat

<b>─── Kunlik Soatlar ───</b>
"""
    
    for record in work_records:
        report += f"\n{format_date(record['work_date'])}: {record['hours']} soat"
    
    report += f"""

<b>─── Jami ───</b>
<b>Jami soat:</b> {total_hours} soat
<b>Ish haqi:</b> {total_salary:,.0f} so'm
"""
    
    await message.answer(report, parse_mode="HTML", reply_markup=get_employee_menu())
    await state.set_state(EmployeeMenu.main)


# ===================== BOSS: XODIMLAR VAQTINI KO'RISH =====================

@dp.message(BossMenu.main, F.text == "📊 Xodimlar vaqtini ko'rish")
async def boss_view_employee_hours(message: types.Message, state: FSMContext):
    """Barcha xodimlarning vaqtini ko'rish"""
    employees = db.get_all_employees()
    
    if not employees:
        await message.answer(
            "📭 Hali faol xodim yo'q.",
            reply_markup=get_boss_menu()
        )
        return
    
    report = "📊 <b>Xodimlar Ish Vaqti</b>\n\n"
    
    for emp in employees:
        work_records = db.get_work_hours(emp['user_id'])
        
        if work_records:
            total_hours = sum(record['hours'] for record in work_records)
            report += f"<b>{emp['full_name']}</b> ({emp['hourly_rate']} so'm/soat)\n"
            
            for record in work_records:
                report += f"  • {format_date(record['work_date'])}: {record['hours']} soat\n"
            
            report += f"  <b>Jami:</b> {total_hours} soat\n\n"
        else:
            report += f"<b>{emp['full_name']}</b>\n  📭 Vaqt yo'q\n\n"
    
    await message.answer(report, parse_mode="HTML", reply_markup=get_boss_menu())


# ===================== BOSS: VAQT TAHRIRLASH =====================

@dp.message(BossMenu.main, F.text == "✏️ Vaqt tahrirlash / Kiritish")
async def boss_edit_hours_select_employee(message: types.Message, state: FSMContext):
    """Tahrirlash uchun xodim tanlash"""
    employees = db.get_all_employees()
    
    if not employees:
        await message.answer(
            "📭 Hali faol xodim yo'q.",
            reply_markup=get_boss_menu()
        )
        return
    
    # Inline tugmalar yaratish
    buttons = []
    for emp in employees:
        buttons.append([
            InlineKeyboardButton(
                text=emp['full_name'],
                callback_data=f"edit_employee:{emp['user_id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "✏️ <b>Xodimni tanlang</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(BossMenu.choosing_employee_for_edit)


@dp.callback_query(F.data.startswith("edit_employee:"))
async def boss_edit_employee_enter_date(callback: types.CallbackQuery, state: FSMContext):
    """Tahrirlash uchun sanani so'rash"""
    employee_id = int(callback.data.split(":")[1])
    employee = db.get_user(employee_id)
    
    await state.update_data(edit_employee_id=employee_id)
    await state.set_state(BossMenu.waiting_edit_date)
    
    await callback.message.edit_text(
        f"📅 <b>{employee['full_name']} uchun sana kiriting</b>\n\n"
        f"Format: DD.MM.YYYY",
        parse_mode="HTML"
    )


@dp.message(BossMenu.waiting_edit_date)
async def boss_edit_employee_enter_hours(message: types.Message, state: FSMContext):
    """Tahrirlash uchun soatni so'rash"""
    try:
        date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")
        
        await state.update_data(edit_date=date_str)
        await state.set_state(BossMenu.waiting_edit_hours)
        
        await message.answer(
            f"⏱️ <b>Soatni kiriting</b>\n\n"
            f"Sana: {format_date(date_str)}\n"
            f"Masalan: 8 yoki 7.5",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri format. DD.MM.YYYY formatida kiriting.")


@dp.message(BossMenu.waiting_edit_hours)
async def boss_save_edited_hours(message: types.Message, state: FSMContext):
    """Tahrirlangan vaqtni saqlash"""
    hours_text = message.text.strip()
    
    if not is_valid_hours(hours_text):
        await message.answer("❌ Iltimos, to'g'ri raqam kiriting (0-24 orasida).")
        return
    
    hours = float(hours_text)
    data = await state.get_data()
    
    employee_id = data['edit_employee_id']
    edit_date = data['edit_date']
    
    # Mavjudmi tekshirish
    existing = db.get_work_hours(employee_id, edit_date)
    
    if existing:
        # Yangilash
        db.update_work_hours(employee_id, edit_date, hours)
        message_text = "Yangilandi ✅"
    else:
        # Yangi kiritish
        success, msg = db.add_work_hours(employee_id, edit_date, hours)
        if not success:
            await message.answer(f"❌ {msg}", reply_markup=get_boss_menu())
            await state.set_state(BossMenu.main)
            return
        message_text = "Kiritildi ✅"
    
    employee = db.get_user(employee_id)
    
    await message.answer(
        f"{message_text}\n\n"
        f"<b>Xodim:</b> {employee['full_name']}\n"
        f"<b>Sana:</b> {format_date(edit_date)}\n"
        f"<b>Soat:</b> {hours} soat",
        parse_mode="HTML",
        reply_markup=get_boss_menu()
    )
    
    await state.set_state(BossMenu.main)


# ===================== BOSS: UMUMIY HISOBOT =====================

@dp.message(BossMenu.main, F.text == "💰 Umumiy Hisobot (Summa)")
async def boss_request_report_date_range(message: types.Message, state: FSMContext):
    """Umumiy hisobot uchun vaqt oralig'i so'rash"""
    await message.answer(
        "💰 <b>Umumiy Hisobot</b>\n\n"
        "Sana oralig'ini kiriting (Format: DD.MM.YYYY-DD.MM.YYYY)\n\n"
        "Masalan: 10.06.2026-13.07.2026",
        parse_mode="HTML"
    )
    await state.set_state(BossMenu.waiting_report_date_range)


@dp.message(BossMenu.waiting_report_date_range)
async def boss_generate_report(message: types.Message, state: FSMContext):
    """Umumiy hisob-kitobi yaratish"""
    date_range = parse_date_range(message.text)
    
    if not date_range:
        await message.answer(
            "❌ Xato format.\n\n"
            "Iltimos, DD.MM.YYYY-DD.MM.YYYY formatida kiriting.\n"
            "Masalan: 10.06.2026-13.07.2026"
        )
        return
    
    start_date, end_date = date_range
    
    # Barcha xodimlarning vaqtini olish
    work_records = db.get_all_work_hours_range(start_date, end_date)
    
    if not work_records:
        await message.answer(
            f"📭 Bu oraliqda hech qanday ish vaqti kiritilmagan.\n\n"
            f"<b>Oralig'i:</b> {format_date(start_date)} - {format_date(end_date)}",
            parse_mode="HTML",
            reply_markup=get_boss_menu()
        )
        await state.set_state(BossMenu.main)
        return
    
    # Ma'lumotlarni guruhlash
    employee_data = {}
    for record in work_records:
        emp_id = record['user_id']
        if emp_id not in employee_data:
            employee_data[emp_id] = {
                'name': record['full_name'],
                'hourly_rate': record['hourly_rate'],
                'records': [],
                'total_hours': 0
            }
        employee_data[emp_id]['records'].append(record)
        employee_data[emp_id]['total_hours'] += record['hours']
    
    # Hisobotni formatlash
    report = f"""
💰 <b>Umumiy Ish Haqi Hisoboti</b>

<b>Oralig'i:</b> {format_date(start_date)} - {format_date(end_date)}

"""
    
    total_company_salary = 0
    
    for emp_id, data in employee_data.items():
        emp_salary = data['total_hours'] * data['hourly_rate']
        total_company_salary += emp_salary
        
        report += f"<b>{data['name']}</b>\n"
        report += f"  Soatbay haq: {data['hourly_rate']} so'm\n"
        report += f"  Jami soat: {data['total_hours']} soat\n"
        report += f"  <b>To'lash summa: {emp_salary:,.0f} so'm</b>\n\n"
    
    report += f"""
<b>═══════════════════════</b>
<b>Korxona bo'yicha jami xarajat:</b> {total_company_salary:,.0f} so'm
"""
    
    await message.answer(report, parse_mode="HTML", reply_markup=get_boss_menu())
    await state.set_state(BossMenu.main)


# ===================== BEKOR QILISH =====================

@dp.callback_query(F.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    """Amaliyotni bekor qilish"""
    await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=None)
    
    user = db.get_user(callback.from_user.id)
    if user and user['role'] == ROLE_BOSS:
        await state.set_state(BossMenu.main)
    else:
        await state.set_state(EmployeeMenu.main)


# ===================== XODIM MENYUSI =====================

@dp.message(EmployeeMenu.main)
async def employee_menu_handler(message: types.Message, state: FSMContext):
    """Xodim menyusi orta turgan xabarlarni qayta tekshirish"""
    await message.answer(
        "❓ Noma'lum buyruq. Iltimos, tugmalardan birini tanlang.",
        reply_markup=get_employee_menu()
    )


# ===================== BOSS MENYUSI =====================

@dp.message(BossMenu.main)
async def boss_menu_handler(message: types.Message, state: FSMContext):
    """Boss menyusi orta turgan xabarlarni qayta tekshirish"""
    await message.answer(
        "❓ Noma'lum buyruq. Iltimos, tugmalardan birini tanlang.",
        reply_markup=get_boss_menu()
    )


# ===================== BOT ISHGA TUSHIRISH =====================

async def main():
    """Botni ishga tushirish"""
    print("🤖 Bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
