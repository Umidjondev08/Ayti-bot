"""
💻 IT Ta'lim Markazi Boti
Ustoz: Muhammad Abdulloh
Professional ta'lim boshqaruv tizimi
"""

import logging
import sqlite3
import asyncio
import sys
from datetime import datetime, date
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
    ContextTypes
)

# ══════════════════════════════════════════
#              SOZLAMALAR
# ══════════════════════════════════════════
BOT_TOKEN    = "8686865318:AAEK4NOQjJDOlCqLKfnEaPrbgmzww8ga0Ao"
CHANNEL_ID   = "@dasturchilar_uchun_foydali"
ADMIN_IDS    = [7160654862]
TEACHER_NAME = "Zokirov Raxmatillo"

LEVELS = {
    "python":    "🐍 Python dasturlash",
    "frontend":  "🌐 Frontend (HTML/CSS/JS)",
    "backend":   "⚙️ Backend Development",
    "fullstack": "🚀 Full Stack Development",
}

LEVEL_SCHEDULE = {
    "python":    3,
    "frontend":  3,
    "backend":   4,
    "fullstack": 5,
}

(
    REG_NAME, REG_PHONE, REG_LEVEL,
    ABSENT_REASON_CHOICE, ABSENT_TEXT,
    TASK_WAIT,
    ADMIN_TEST_LEVEL, ADMIN_TEST_QUESTION,
    ADMIN_TEST_OPTIONS, ADMIN_TEST_ANSWER,
    ADMIN_BROADCAST,
) = range(11)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)

def init_db():
    conn = sqlite3.connect("it_bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT,
        full_name TEXT, phone TEXT, level TEXT, registered_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        date TEXT, status TEXT, reason TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        file_id TEXT, file_type TEXT, caption TEXT,
        grade INTEGER, grade_comment TEXT, submitted_at TEXT, graded_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT,
        question TEXT, option_a TEXT, option_b TEXT,
        option_c TEXT, option_d TEXT, correct TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        test_id INTEGER, answer TEXT, is_correct INTEGER, answered_at TEXT)""")
    conn.commit(); conn.close()

def db():
    return sqlite3.connect("it_bot.db")

def is_registered(uid):
    c = db(); cur = c.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone(); c.close(); return r is not None

def is_admin(uid):
    return uid in ADMIN_IDS

def get_user(uid):
    c = db(); cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone(); c.close(); return r

def get_level(uid):
    c = db(); cur = c.cursor()
    cur.execute("SELECT level FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone(); c.close()
    return r[0] if r else None

def main_menu(uid):
    rows = [
        [KeyboardButton("✅ Keldim"), KeyboardButton("❌ Kelmadim")],
        [KeyboardButton("📝 Vazifa yuborish"), KeyboardButton("🧪 Test ishlash")],
        [KeyboardButton("📊 Mening natijalarim"), KeyboardButton("💻 Mening yo'nalishim")],
    ]
    if is_admin(uid):
        rows.append([KeyboardButton("⚙️ Admin panel")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def check_sub(bot, uid):
    try:
        m = await bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ("member", "administrator", "creator")
    except:
        return False

def level_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐍 Python dasturlash — Boshlang'ichdan",   callback_data="lvl_python")],
        [InlineKeyboardButton("🌐 Frontend — HTML/CSS/JS",                callback_data="lvl_frontend")],
        [InlineKeyboardButton("⚙️ Backend — Server va API",               callback_data="lvl_backend")],
        [InlineKeyboardButton("🚀 Full Stack — To'liq dasturlash",        callback_data="lvl_fullstack")],
    ])

# ── START ────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = user.id

    subbed = await check_sub(ctx.bot, uid)
    if not subbed:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish",
                                  url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")],
            [InlineKeyboardButton("✅ Obuna bo'ldim, tekshir", callback_data="check_sub")],
        ])
        await update.message.reply_text(
            f"💻 *Salom, {user.first_name}!*\n\n"
            f"Xush kelibsiz — *Ustoz {TEACHER_NAME}*ning\n"
            f"IT ta'lim markaziga!\n\n"
            f"Botdan foydalanish uchun avval kanalga obuna bo'ling 👇",
            parse_mode="Markdown", reply_markup=kb
        )
        return ConversationHandler.END

    if is_registered(uid):
        u = get_user(uid)
        lvl = LEVELS.get(u[4], u[4])
        await update.message.reply_text(
            f"💻 *Salom, {u[2]}!*\n"
            f"Xush kelibsiz qaytib! 🎉\n\n"
            f"🖥 Yo'nalishingiz: *{lvl}*\n"
            f"Ustoz {TEACHER_NAME} darslariga omad! 💪",
            parse_mode="Markdown", reply_markup=main_menu(uid)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"💻 *Salom, {user.first_name}!*\n\n"
            f"Xush kelibsiz — *Ustoz {TEACHER_NAME}*ning\n"
            f"IT ta'lim markaziga! 🎓\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 Ro'yxatdan o'tish uchun\n"
            f"to'liq *Ism va Familiyangizni* kiriting:\n"
            f"_(Masalan: Abdullayev Jasur)_",
            parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
        )
        return REG_NAME

async def check_sub_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = query.from_user.id

    subbed = await check_sub(ctx.bot, uid)
    if not subbed:
        await query.answer("Hali obuna bo'lmadingiz! Iltimos obuna bo'ling.", show_alert=True)
        return ConversationHandler.END

    await query.answer("Obuna tasdiqlandi!")

    if is_registered(uid):
        u = get_user(uid)
        await query.message.reply_text(
            f"✅ *Obuna tasdiqlandi!*\n\n"
            f"💻 Xush kelibsiz, *{u[2]}*! 🎉",
            parse_mode="Markdown", reply_markup=main_menu(uid)
        )
        return ConversationHandler.END
    else:
        await query.message.reply_text(
            f"✅ *Obuna tasdiqlandi!*\n\n"
            f"💻 Xush kelibsiz — *Ustoz {TEACHER_NAME}*ning\n"
            f"IT ta'lim markaziga! 🎓\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 To'liq *Ism va Familiyangizni* kiriting:\n"
            f"_(Masalan: Abdullayev Jasur)_",
            parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
        )
        return REG_NAME

# ── RO'YXATDAN O'TISH ────────────────────
async def reg_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 4 or len(name.split()) < 2:
        await update.message.reply_text(
            "Iltimos *to'liq ism va familiyangizni* kiriting:\n_(Masalan: Abdullayev Jasur)_",
            parse_mode="Markdown"
        )
        return REG_NAME

    ctx.user_data["reg_name"] = name
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Raqamni avtomatik ulashish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        f"✅ *Ism:* {name}\n\n"
        f"📱 Telefon raqamingizni yuboring:\n_(Pastdagi tugma yoki +998901234567)_",
        parse_mode="Markdown", reply_markup=kb
    )
    return REG_PHONE

async def reg_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"): phone = "+" + phone
    else:
        phone = update.message.text.strip()
        if not (phone.startswith("+") and len(phone) >= 10):
            await update.message.reply_text(
                "Noto'g'ri format. *+998XXXXXXXXX* shaklida kiriting:",
                parse_mode="Markdown"
            )
            return REG_PHONE

    ctx.user_data["reg_phone"] = phone
    await update.message.reply_text(
        f"✅ *Raqam:* {phone}\n\n"
        f"🖥 IT yo'nalishingizni tanlang:\n\n"
        f"🐍 *Python* — Dasturlashni noldan o'rganmoqchi\n"
        f"🌐 *Frontend* — Sayt dizayni va interfeys\n"
        f"⚙️ *Backend* — Server, API, ma'lumotlar bazasi\n"
        f"🚀 *Full Stack* — Hammasi: frontend + backend",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text("👇 Yo'nalishingizni tanlang:", reply_markup=level_keyboard())
    return REG_LEVEL

async def reg_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = query.data.split("_")[1]
    uid   = query.from_user.id

    conn = db(); c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO users (user_id,username,full_name,phone,level,registered_at) VALUES (?,?,?,?,?,?)",
        (uid, query.from_user.username, ctx.user_data["reg_name"],
         ctx.user_data["reg_phone"], level, datetime.now().isoformat())
    )
    conn.commit(); conn.close()

    lvl_text  = LEVELS[level]
    week_days = LEVEL_SCHEDULE[level]

    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                aid,
                f"🆕 Yangi o'quvchi ro'yxatdan o'tdi!\n\n"
                f"👤 {ctx.user_data['reg_name']}\n"
                f"📱 {ctx.user_data['reg_phone']}\n"
                f"💻 {lvl_text}\n"
                f"🆔 {uid}",
            )
        except: pass

    await query.message.reply_text(
        f"🎉 *Tabriklaymiz! Ro'yxat yakunlandi!*\n\n"
        f"┌─────────────────────────\n"
        f"│ 👤 {ctx.user_data['reg_name']}\n"
        f"│ 📱 {ctx.user_data['reg_phone']}\n"
        f"│ 💻 {lvl_text}\n"
        f"│ 📅 Haftada {week_days} kun dars\n"
        f"└─────────────────────────\n\n"
        f"🖥 *Ustoz {TEACHER_NAME}*ning IT darslariga\n"
        f"xush kelibsiz! Muvaffaqiyat! 💪",
        parse_mode="Markdown", reply_markup=main_menu(uid)
    )
    return ConversationHandler.END

# ── DAVOMAT ──────────────────────────────
async def came(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_registered(uid):
        await update.message.reply_text("Avval ro'yxatdan o'ting: /start"); return

    today = date.today().isoformat()
    conn = db(); c = conn.cursor()
    c.execute("SELECT status FROM attendance WHERE user_id=? AND date=?", (uid, today))
    existing = c.fetchone()
    if existing:
        icon = "✅" if existing[0] == "came" else "❌"
        await update.message.reply_text(f"Siz bugun allaqachon belgiladingiz: {icon}")
        conn.close(); return

    c.execute("INSERT INTO attendance (user_id,date,status,created_at) VALUES (?,?,?,?)",
              (uid, today, "came", datetime.now().isoformat()))
    conn.commit(); conn.close()

    u = get_user(uid)
    now = datetime.now().strftime("%H:%M")
    await update.message.reply_text(
        f"✅ *Davomat belgilandi!*\n\n"
        f"│ 📅 {today}  🕐 {now}\n"
        f"│ 👤 {u[2]}\n"
        f"│ 💻 {LEVELS.get(u[4], u[4])}\n\n"
        f"Darsda omad! 🚀",
        parse_mode="Markdown"
    )

async def absent_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_registered(uid):
        await update.message.reply_text("Avval ro'yxatdan o'ting: /start"); return

    today = date.today().isoformat()
    conn = db(); c = conn.cursor()
    c.execute("SELECT status FROM attendance WHERE user_id=? AND date=?", (uid, today))
    existing = c.fetchone(); conn.close()
    if existing:
        icon = "✅" if existing[0] == "came" else "❌"
        await update.message.reply_text(f"Siz bugun allaqachon belgiladingiz: {icon}")
        return ConversationHandler.END

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Sababli (sabab yozaman)", callback_data="abs_reason")],
        [InlineKeyboardButton("🚫 Sababsiz",                callback_data="abs_noreason")],
    ])
    await update.message.reply_text(
        "❌ *Kelmadingiz deb belgilanmoqda...*\n\nSababli yoki sababsizmi?",
        parse_mode="Markdown", reply_markup=kb
    )
    return ABSENT_REASON_CHOICE

async def absent_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["abs_type"] = query.data
    if query.data == "abs_reason":
        await query.message.reply_text(
            "✍️ *Sabab yozing:*\n_(Matn, rasm yoki ovozli xabar)_",
            parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
        )
    else:
        await query.message.reply_text(
            "✍️ *Qisqacha tushuntiring:*\n_(Nega kelolmadingiz?)_",
            parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
        )
    return ABSENT_TEXT

async def absent_text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    today = date.today().isoformat()
    msg   = update.message
    label = "Sababli" if ctx.user_data.get("abs_type") == "abs_reason" else "Sababsiz"

    if msg.text:     reason = msg.text
    elif msg.photo:  reason = f"[Rasm] {msg.caption or ''}"
    elif msg.voice:  reason = "[Ovozli xabar]"
    elif msg.document: reason = f"[Fayl: {msg.document.file_name}]"
    else:            reason = "[Media]"

    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO attendance (user_id,date,status,reason,created_at) VALUES (?,?,?,?,?)",
              (uid, today, "absent", f"[{label}] {reason}", datetime.now().isoformat()))
    conn.commit(); conn.close()

    u = get_user(uid)
    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                aid,
                f"🔴 *Kelmadi bildirishi*\n\n"
                f"│ 👤 {u[2]}  📱 {u[3]}\n"
                f"│ 💻 {LEVELS.get(u[4], u[4])}\n"
                f"│ 📅 {today}  🏷 {label}\n"
                f"│ 📌 {reason}",
                parse_mode="Markdown"
            )
        except: pass

    await update.message.reply_text(
        f"✅ *Qayd etildi*\n\n│ 📅 {today}\n│ 🏷 {label}\n│ 📌 {reason}\n\nO'qituvchiga xabar yuborildi.",
        parse_mode="Markdown", reply_markup=main_menu(uid)
    )
    return ConversationHandler.END

# ── VAZIFA ───────────────────────────────
async def task_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_registered(uid):
        await update.message.reply_text("Avval ro'yxatdan o'ting: /start"); return
    await update.message.reply_text(
        "📤 *Vazifangizni yuboring*\n\nKod fayli, rasm, video yoki matn.\nBekor qilish: /cancel",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return TASK_WAIT

async def task_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message
    file_id = file_type = None
    caption = msg.caption or ""

    if msg.document:   file_id, file_type = msg.document.file_id, "document"
    elif msg.photo:    file_id, file_type = msg.photo[-1].file_id, "photo"
    elif msg.video:    file_id, file_type = msg.video.file_id, "video"
    elif msg.text:     file_type, caption = "text", msg.text
    else:
        await update.message.reply_text("Bu turdagi fayl qabul qilinmaydi."); return TASK_WAIT

    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id,file_id,file_type,caption,submitted_at) VALUES (?,?,?,?,?)",
              (uid, file_id, file_type, caption, datetime.now().isoformat()))
    tid = c.lastrowid; conn.commit(); conn.close()

    u = get_user(uid)
    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                aid,
                f"📬 *Yangi vazifa keldi!*\n\n"
                f"│ 👤 {u[2]}  📱 {u[3]}\n"
                f"│ 💻 {LEVELS.get(u[4], u[4])}\n"
                f"│ 🆔 Vazifa #{tid}  📎 {file_type}\n"
                f"│ 🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                f"│ 📝 {caption or '—'}",
                parse_mode="Markdown"
            )
            if file_id:
                send = {"photo": ctx.bot.send_photo, "document": ctx.bot.send_document, "video": ctx.bot.send_video}.get(file_type)
                if send:
                    kb = InlineKeyboardMarkup([[
                        InlineKeyboardButton("1⭐️", callback_data=f"grd_{tid}_1"),
                        InlineKeyboardButton("2⭐️", callback_data=f"grd_{tid}_2"),
                        InlineKeyboardButton("3⭐️", callback_data=f"grd_{tid}_3"),
                        InlineKeyboardButton("4⭐️", callback_data=f"grd_{tid}_4"),
                        InlineKeyboardButton("5⭐️", callback_data=f"grd_{tid}_5"),
                    ]])
                    await send(aid, file_id, caption=f"Vazifa #{tid} | {u[2]}", reply_markup=kb)
        except: pass

    await update.message.reply_text(
        f"✅ *Vazifa yuborildi!*\n\n│ 🆔 Vazifa #{tid}\n│ 🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\nO'qituvchi tekshirgach baho qo'yadi 👨‍💻",
        parse_mode="Markdown", reply_markup=main_menu(uid)
    )
    return ConversationHandler.END

# ── TEST ─────────────────────────────────
async def test_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_registered(uid):
        await update.message.reply_text("Avval ro'yxatdan o'ting: /start"); return

    level = get_level(uid)
    conn = db(); c = conn.cursor()
    c.execute("""SELECT t.id,t.question,t.option_a,t.option_b,t.option_c,t.option_d
        FROM tests t WHERE t.level=? AND t.id NOT IN
        (SELECT test_id FROM test_results WHERE user_id=?) ORDER BY t.id LIMIT 1""", (level, uid))
    test = c.fetchone()
    c.execute("SELECT COUNT(*),SUM(is_correct) FROM test_results WHERE user_id=?", (uid,))
    stats = c.fetchone(); conn.close()

    if not test:
        await update.message.reply_text(
            "📭 *Hozircha yangi testlar yo'q!*\n\nO'qituvchi tez orada qo'shadi. 😊",
            parse_mode="Markdown", reply_markup=main_menu(uid)
        )
        return

    tid, question, a, b, cv, d = test
    ctx.user_data["current_test"] = tid
    total, ok = stats[0] or 0, stats[1] or 0

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🅐  {a}",  callback_data="ans_A")],
        [InlineKeyboardButton(f"🅑  {b}",  callback_data="ans_B")],
        [InlineKeyboardButton(f"🅒  {cv}", callback_data="ans_C")],
        [InlineKeyboardButton(f"🅓  {d}",  callback_data="ans_D")],
    ])
    await update.message.reply_text(
        f"🧪 *Test #{tid}*  |  💻 {LEVELS.get(level, level)}\n"
        f"📊 Jami: {total} | To'g'ri: {ok} ta\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n❓ *{question}*",
        parse_mode="Markdown", reply_markup=kb
    )

async def test_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid    = query.from_user.id
    answer = query.data.split("_")[1]
    tid    = ctx.user_data.get("current_test")
    if not tid: return

    conn = db(); c = conn.cursor()
    c.execute("SELECT correct,question,option_a,option_b,option_c,option_d FROM tests WHERE id=?", (tid,))
    row = c.fetchone()
    if not row: conn.close(); return

    correct, question, a, b, cv, d = row
    is_correct = 1 if answer == correct.upper() else 0
    c.execute("INSERT INTO test_results (user_id,test_id,answer,is_correct,answered_at) VALUES (?,?,?,?,?)",
              (uid, tid, answer, is_correct, datetime.now().isoformat()))
    conn.commit()
    c.execute("SELECT COUNT(*),SUM(is_correct) FROM test_results WHERE user_id=?", (uid,))
    stats = c.fetchone(); conn.close()
    total, ok = stats[0] or 0, stats[1] or 0
    opts = {"A": a, "B": b, "C": cv, "D": d}
    pct = round(ok / total * 100) if total else 0

    if is_correct:
        result = f"✅ *To'g'ri! Ajoyib!* 🎉\nJavob: *{correct}) {opts[correct.upper()]}*"
    else:
        result = f"❌ *Noto'g'ri!*\nSiz: *{answer}) {opts[answer]}*\nTo'g'ri: *{correct}) {opts[correct.upper()]}*"

    await query.message.edit_text(
        f"🧪 *Test #{tid}*\n━━━━━━━━━━━━━━━━━━━━\n❓ {question}\n\n{result}\n\n📊 {ok}/{total} ({pct}%) ✅",
        parse_mode="Markdown"
    )

# ── NATIJALAR ────────────────────────────
async def my_results(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_registered(uid):
        await update.message.reply_text("Avval ro'yxatdan o'ting: /start"); return

    u = get_user(uid)
    conn = db(); c = conn.cursor()
    c.execute("SELECT status,COUNT(*) FROM attendance WHERE user_id=? GROUP BY status", (uid,))
    att = dict(c.fetchall())
    came_n = att.get("came", 0); absent_n = att.get("absent", 0); total_n = came_n + absent_n
    att_pct = round(came_n / total_n * 100) if total_n else 0

    c.execute("SELECT COUNT(*),SUM(is_correct) FROM test_results WHERE user_id=?", (uid,))
    tr = c.fetchone(); t_total, t_ok = tr[0] or 0, tr[1] or 0
    t_pct = round(t_ok / t_total * 100) if t_total else 0

    c.execute("SELECT grade,grade_comment,submitted_at FROM tasks WHERE user_id=? ORDER BY id DESC LIMIT 5", (uid,))
    tasks = c.fetchall(); conn.close()

    task_lines = ""
    for i, (grade, comment, submitted) in enumerate(tasks, 1):
        g = f"{'⭐️' * grade} ({grade}/5)" if grade else "⏳ Tekshirilmoqda"
        task_lines += f"  {i}. {g}"
        if comment: task_lines += f"\n     💬 _{comment}_"
        task_lines += "\n"

    await update.message.reply_text(
        f"📊 *{u[2]}ning natijalari*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💻 *Yo'nalish:* {LEVELS.get(u[4], u[4])}\n"
        f"📅 *Haftalik dars:* {LEVEL_SCHEDULE.get(u[4], '—')} kun\n\n"
        f"🗓 *Davomat:*\n  ✅ Keldi: *{came_n}* kun  ❌ Kelmadi: *{absent_n}* kun\n  📈 Faollik: *{att_pct}%*\n\n"
        f"🧪 *Testlar:*\n  Jami: *{t_total}* | To'g'ri: *{t_ok}* | *{t_pct}%*\n\n"
        f"📝 *So'ngi vazifalar:*\n{task_lines or '  Hali topshirilmagan'}",
        parse_mode="Markdown"
    )

async def my_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_registered(uid):
        await update.message.reply_text("Avval ro'yxatdan o'ting: /start"); return
    u = get_user(uid)
    await update.message.reply_text(
        f"💻 *Yo'nalishingiz*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷 *{LEVELS.get(u[4], u[4])}*\n"
        f"📅 Haftalik dars: *{LEVEL_SCHEDULE.get(u[4], '—')} kun*\n\n"
        f"*Barcha yo'nalishlar:*\n"
        f"🐍 Python dasturlash — Boshlang'ichdan (3 kun/hafta)\n"
        f"🌐 Frontend — HTML/CSS/JS (3 kun/hafta)\n"
        f"⚙️ Backend — Server va API (4 kun/hafta)\n"
        f"🚀 Full Stack — To'liq dasturlash (5 kun/hafta)\n\n"
        f"Yo'nalishingizni o'zgartirish uchun adminga murojaat qiling.",
        parse_mode="Markdown"
    )

# ── ADMIN PANEL ──────────────────────────
async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("Ruxsat yo'q!"); return

    conn = db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users"); students = c.fetchone()[0]
    c.execute("SELECT level,COUNT(*) FROM users GROUP BY level"); by_level = c.fetchall()
    c.execute("SELECT COUNT(*) FROM tasks WHERE grade IS NULL"); ungraded = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tests"); tests_n = c.fetchone()[0]
    today = date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='came'", (today,)); came_n = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='absent'", (today,)); absent_n = c.fetchone()[0]
    conn.close()

    level_text = ""
    for lvl, cnt in by_level:
        level_text += f"  {LEVELS.get(lvl, lvl)}: *{cnt}* ta\n"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 O'quvchini o'chirish",   callback_data="adm_delete")],
        [InlineKeyboardButton("📅 Bugungi davomat",        callback_data="adm_attendance")],
        [InlineKeyboardButton("👥 O'quvchilar ro'yxati",   callback_data="adm_students")],
        [InlineKeyboardButton("📝 Vazifalarni tekshirish", callback_data="adm_tasks")],
        [InlineKeyboardButton("🧪 Test qo'shish",          callback_data="adm_addtest")],
        [InlineKeyboardButton("📣 Hammaga xabar yuborish", callback_data="adm_broadcast")],
        [InlineKeyboardButton("📊 To'liq statistika",      callback_data="adm_stats")],
    ])

    await update.message.reply_text(
        f"⚙️ *Admin Panel*\nUstoz: *{TEACHER_NAME}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Jami o'quvchi: *{students}* ta\n{level_text}\n"
        f"📅 Bugun ({today}):\n  ✅ Keldi: *{came_n}*  ❌ Kelmadi: *{absent_n}*\n\n"
        f"📝 Tekshirilmagan vazifa: *{ungraded}* ta\n🧪 Jami testlar: *{tests_n}* ta",
        parse_mode="Markdown", reply_markup=kb
    )

# ── O'QUVCHINI O'CHIRISH ─────────────────
async def admin_delete_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """O'quvchilar ro'yxatini ko'rsatish"""
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("Ruxsat yo'q!", show_alert=True); return

    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id, full_name, level FROM users ORDER BY level, full_name")
    students = c.fetchall(); conn.close()

    if not students:
        await query.message.reply_text("Hali o'quvchilar yo'q."); return

    by_lvl = {}
    for uid2, name, lvl in students:
        by_lvl.setdefault(lvl, []).append((uid2, name))

    buttons = []
    for lvl in ["python", "frontend", "backend", "fullstack"]:
        members = by_lvl.get(lvl, [])
        if not members: continue
        buttons.append([InlineKeyboardButton(
            f"── {LEVELS.get(lvl, lvl)} ──", callback_data="noop"
        )])
        for uid2, name in members:
            buttons.append([InlineKeyboardButton(
                f"🗑 {name}", callback_data=f"delstu_{uid2}"
            )])

    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="noop")])

    await query.message.reply_text(
        "🗑 *O'chirish uchun o'quvchini tanlang:*\n\n"
        "_Tugmani bosing — tasdiqlash so'raladi_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def admin_delete_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Tanlangan o'quvchini tasdiqlash"""
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("Ruxsat yo'q!", show_alert=True); return

    target_uid = int(query.data.replace("delstu_", ""))

    conn = db(); c = conn.cursor()
    c.execute("SELECT full_name, phone, level FROM users WHERE user_id=?", (target_uid,))
    row = c.fetchone(); conn.close()

    if not row:
        await query.message.reply_text("❌ O'quvchi topilmadi."); return

    name, phone, lvl = row

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ha, o'chirib tashla!", callback_data=f"delyes_{target_uid}")],
        [InlineKeyboardButton("❌ Bekor qil",           callback_data="noop")],
    ])
    await query.message.reply_text(
        f"⚠️ *Rostdan ham o'chirasizmi?*\n\n"
        f"│ 👤 {name}\n"
        f"│ 📱 {phone}\n"
        f"│ 💻 {LEVELS.get(lvl, lvl)}\n\n"
        f"_Barcha davomat, vazifa va test natijalari ham o'chadi!_",
        parse_mode="Markdown",
        reply_markup=kb
    )

async def admin_delete_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """O'quvchini bazadan o'chirish"""
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("Ruxsat yo'q!", show_alert=True); return

    target_uid = int(query.data.replace("delyes_", ""))

    conn = db(); c = conn.cursor()
    c.execute("SELECT full_name, phone, level FROM users WHERE user_id=?", (target_uid,))
    row = c.fetchone()

    if not row:
        await query.message.edit_text("❌ O'quvchi allaqachon o'chirilgan.")
        conn.close(); return

    name, phone, lvl = row

    # Barcha ma'lumotlarni o'chirish
    c.execute("DELETE FROM users        WHERE user_id=?", (target_uid,))
    c.execute("DELETE FROM attendance   WHERE user_id=?", (target_uid,))
    c.execute("DELETE FROM tasks        WHERE user_id=?", (target_uid,))
    c.execute("DELETE FROM test_results WHERE user_id=?", (target_uid,))
    conn.commit(); conn.close()

    # O'quvchiga xabar yuborish
    try:
        await ctx.bot.send_message(
            target_uid,
            f"ℹ️ Siz IT ta'lim markazidan chiqarib yuborldingiz.\n"
            f"Savollar uchun ustoz {TEACHER_NAME} ga murojaat qiling."
        )
    except:
        pass

    await query.message.edit_text(
        f"✅ *{name} muvaffaqiyatli o'chirildi!*\n\n"
        f"│ 📱 {phone}\n"
        f"│ 💻 {LEVELS.get(lvl, lvl)}\n\n"
        f"_Barcha ma'lumotlari bazadan o'chirildi._",
        parse_mode="Markdown"
    )

async def noop_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

# ── ADMIN CALLBACK ───────────────────────
async def admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    data = query.data
    if not is_admin(uid):
        await query.answer("Ruxsat yo'q!", show_alert=True); return

    conn = db(); c = conn.cursor()

    if data == "adm_attendance":
        today = date.today().isoformat()
        c.execute("SELECT user_id,full_name,level FROM users ORDER BY level")
        all_users = c.fetchall()
        c.execute("SELECT user_id,status,reason FROM attendance WHERE date=?", (today,))
        att_map = {r[0]: (r[1], r[2]) for r in c.fetchall()}
        conn.close()
        if not all_users:
            await query.message.reply_text("Hali o'quvchilar yo'q."); return

        text = f"📅 *Davomat — {today}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        by_lvl = {}
        for uid2, name, lvl in all_users:
            by_lvl.setdefault(lvl, []).append((uid2, name))

        for lvl in ["python", "frontend", "backend", "fullstack"]:
            members = by_lvl.get(lvl, [])
            if not members: continue
            text += f"💻 *{LEVELS.get(lvl, lvl)}*\n"
            for uid2, name in members:
                if uid2 in att_map:
                    status, reason = att_map[uid2]
                    if status == "came":
                        text += f"  ✅ {name}\n"
                    else:
                        r = f" — _{reason}_" if reason else ""
                        text += f"  ❌ {name}{r}\n"
                else:
                    text += f"  ⬜️ {name} (belgilamagan)\n"
            text += "\n"

        came_c   = sum(1 for v in att_map.values() if v[0] == "came")
        absent_c = sum(1 for v in att_map.values() if v[0] == "absent")
        none_c   = len(all_users) - came_c - absent_c
        text += f"━━━━━━━━━━━━━━━━━━━━\n✅ {came_c}  ❌ {absent_c}  ⬜️ {none_c}"
        await query.message.reply_text(text, parse_mode="Markdown")

    elif data == "adm_students":
        c.execute("SELECT full_name,phone,level,registered_at FROM users ORDER BY level,full_name")
        rows = c.fetchall(); conn.close()
        if not rows:
            await query.message.reply_text("Hali o'quvchilar yo'q."); return
        by_lvl = {}
        for name, phone, lvl, reg in rows:
            by_lvl.setdefault(lvl, []).append((name, phone, reg))
        text = "👥 *O'quvchilar ro'yxati*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        total = 0
        for lvl in ["python", "frontend", "backend", "fullstack"]:
            members = by_lvl.get(lvl, [])
            if not members: continue
            text += f"💻 *{LEVELS.get(lvl, lvl)}* — {len(members)} ta\n"
            for i, (name, phone, reg) in enumerate(members, 1):
                text += f"  {i}. {name} | {phone} | {(reg or '')[:10]}\n"
            text += "\n"; total += len(members)
        text += f"*Jami: {total} ta*"
        await query.message.reply_text(text, parse_mode="Markdown")

    elif data == "adm_tasks":
        c.execute("""SELECT t.id,u.full_name,u.level,t.file_type,t.caption,t.submitted_at
            FROM tasks t JOIN users u ON t.user_id=u.user_id
            WHERE t.grade IS NULL ORDER BY t.submitted_at DESC LIMIT 10""")
        rows = c.fetchall(); conn.close()
        if not rows:
            await query.message.reply_text("✅ Barcha vazifalar baholangan!"); return
        for tid, name, lvl, ftype, caption, submitted in rows:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("1⭐️", callback_data=f"grd_{tid}_1"),
                InlineKeyboardButton("2⭐️", callback_data=f"grd_{tid}_2"),
                InlineKeyboardButton("3⭐️", callback_data=f"grd_{tid}_3"),
                InlineKeyboardButton("4⭐️", callback_data=f"grd_{tid}_4"),
                InlineKeyboardButton("5⭐️", callback_data=f"grd_{tid}_5"),
            ]])
            await query.message.reply_text(
                f"📝 *Vazifa #{tid}*\n│ 👤 {name}\n│ 💻 {LEVELS.get(lvl, lvl)}\n│ 📎 {ftype}  🕐 {submitted[:16]}\n│ 📌 {caption or '—'}\n\nBaho qo'ying:",
                parse_mode="Markdown", reply_markup=kb
            )

    elif data == "adm_stats":
        c.execute("SELECT COUNT(*) FROM users"); tu = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM attendance WHERE status='came'"); tc = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM attendance WHERE status='absent'"); ta = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM test_results"); tt = c.fetchone()[0]
        c.execute("SELECT SUM(is_correct) FROM test_results"); tok = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM tasks WHERE grade IS NOT NULL"); tg = c.fetchone()[0]
        c.execute("SELECT AVG(grade) FROM tasks WHERE grade IS NOT NULL"); avg_g = c.fetchone()[0]
        conn.close()
        await query.message.reply_text(
            f"📊 *Umumiy statistika*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Jami o'quvchi: *{tu}* ta\n\n"
            f"📅 *Davomat:*\n  ✅ Jami keldi: *{tc}*  ❌ Kelmadi: *{ta}*\n\n"
            f"🧪 *Testlar:*\n  Jami: *{tt}*  To'g'ri: *{tok}*  Foiz: *{round(tok/tt*100) if tt else 0}%*\n\n"
            f"📝 *Vazifalar:*\n  Baholangan: *{tg}*  O'rtacha: *{round(avg_g, 1) if avg_g else '—'}*/5",
            parse_mode="Markdown"
        )

    elif data == "adm_broadcast":
        conn.close()
        await query.message.reply_text(
            "📣 *Hammaga xabar yuborish*\n\nMatn, rasm yoki fayl yuboring.\nBekor qilish: /cancel",
            parse_mode="Markdown"
        )
        return ADMIN_BROADCAST

    elif data == "adm_addtest":
        conn.close()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🐍 Python",    callback_data="tst_python"),
             InlineKeyboardButton("🌐 Frontend",  callback_data="tst_frontend")],
            [InlineKeyboardButton("⚙️ Backend",   callback_data="tst_backend"),
             InlineKeyboardButton("🚀 Full Stack", callback_data="tst_fullstack")],
        ])
        await query.message.reply_text("🧪 *Yangi test — yo'nalish tanlang:*", parse_mode="Markdown", reply_markup=kb)
        return ADMIN_TEST_LEVEL

    else:
        conn.close()

async def admin_grade(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return
    _, tid, grade = query.data.split("_")
    tid, grade = int(tid), int(grade)
    conn = db(); c = conn.cursor()
    c.execute("UPDATE tasks SET grade=?,graded_at=? WHERE id=?", (grade, datetime.now().isoformat(), tid))
    c.execute("SELECT user_id,caption FROM tasks WHERE id=?", (tid,))
    row = c.fetchone(); conn.commit(); conn.close()
    stars = "⭐️" * grade
    if row:
        try:
            await ctx.bot.send_message(
                row[0],
                f"🎓 *Vazifangiz baholandi!*\n━━━━━━━━━━━━━━━━━━━━\n\n"
                f"│ 🆔 Vazifa #{tid}\n│ 📌 {row[1] or '—'}\n│ 🎯 Baho: *{grade}/5* {stars}\n\n"
                f"Ustoz {TEACHER_NAME} tomonidan baholandi.\nDavom eting! 💪",
                parse_mode="Markdown"
            )
        except: pass
    await query.message.edit_text(
        query.message.text + f"\n\n✅ *Baho qo'yildi: {grade}/5 {stars}*",
        parse_mode="Markdown"
    )

# ── BROADCAST ────────────────────────────
async def broadcast_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid): return ConversationHandler.END

    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id FROM users"); all_uids = [r[0] for r in c.fetchall()]
    conn.close()

    msg = update.message; sent = failed = 0
    for tuid in all_uids:
        try:
            if msg.text:
                await ctx.bot.send_message(tuid, f"📣 *Ustoz {TEACHER_NAME} dan xabar:*\n\n{msg.text}", parse_mode="Markdown")
            elif msg.photo:
                await ctx.bot.send_photo(tuid, msg.photo[-1].file_id, caption=f"📣 Ustoz {TEACHER_NAME}:\n{msg.caption or ''}")
            elif msg.document:
                await ctx.bot.send_document(tuid, msg.document.file_id, caption=f"📣 Ustoz {TEACHER_NAME}:\n{msg.caption or ''}")
            elif msg.video:
                await ctx.bot.send_video(tuid, msg.video.file_id, caption=f"📣 Ustoz {TEACHER_NAME}:\n{msg.caption or ''}")
            sent += 1
        except: failed += 1

    await update.message.reply_text(
        f"✅ *Xabar yuborildi!*\n\n│ ✅ Muvaffaqiyatli: *{sent}* ta\n│ ❌ Xatolik: *{failed}* ta",
        parse_mode="Markdown", reply_markup=main_menu(uid)
    )
    return ConversationHandler.END

# ── ADMIN TEST QO'SHISH ──────────────────
async def admin_test_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = query.data.split("_")[1]
    ctx.user_data["test_level"] = level
    ctx.user_data["test_options"] = []
    await query.message.reply_text(
        f"🧪 *Test — {LEVELS.get(level, level)}*\n\nSavolni yozing:",
        parse_mode="Markdown"
    )
    return ADMIN_TEST_QUESTION

async def admin_test_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["test_question"] = update.message.text
    await update.message.reply_text("✅ Savol qabul qilindi.\n\n🅐 *A varianti:*", parse_mode="Markdown")
    return ADMIN_TEST_OPTIONS

async def admin_test_options(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    opts = ctx.user_data.get("test_options", [])
    labels = ["A", "B", "C", "D"]
    opts.append(update.message.text)
    ctx.user_data["test_options"] = opts
    if len(opts) < 4:
        await update.message.reply_text(f"✅ Qabul qilindi.\n\n*{labels[len(opts)]} varianti:*", parse_mode="Markdown")
        return ADMIN_TEST_OPTIONS
    else:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("A", callback_data="cor_A"),
            InlineKeyboardButton("B", callback_data="cor_B"),
            InlineKeyboardButton("C", callback_data="cor_C"),
            InlineKeyboardButton("D", callback_data="cor_D"),
        ]])
        q = ctx.user_data["test_question"]
        await update.message.reply_text(
            f"✅ *Variantlar tayyor!*\n\n❓ {q}\n\nA) {opts[0]}\nB) {opts[1]}\nC) {opts[2]}\nD) {opts[3]}\n\n✅ *To'g'ri javobni tanlang:*",
            parse_mode="Markdown", reply_markup=kb
        )
        return ADMIN_TEST_ANSWER

async def admin_test_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    correct  = query.data.split("_")[1]
    opts     = ctx.user_data["test_options"]
    level    = ctx.user_data["test_level"]
    question = ctx.user_data["test_question"]

    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO tests (level,question,option_a,option_b,option_c,option_d,correct,created_at) VALUES (?,?,?,?,?,?,?,?)",
              (level, question, opts[0], opts[1], opts[2], opts[3], correct, datetime.now().isoformat()))
    conn.commit(); conn.close()
    ctx.user_data["test_options"] = []; ctx.user_data["test_question"] = ""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yana test qo'shish", callback_data="adm_addtest")],
        [InlineKeyboardButton("✅ Tugatish",            callback_data="adm_done")],
    ])
    await query.message.reply_text(
        f"✅ *Test saqlandi!*\n\n💻 {LEVELS.get(level, level)}\n❓ {question}\n✅ To'g'ri javob: *{correct}*",
        parse_mode="Markdown", reply_markup=kb
    )
    return ConversationHandler.END

async def admin_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✅ Tayyor!", reply_markup=main_menu(query.from_user.id))
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Bekor qilindi.", reply_markup=main_menu(update.effective_user.id))
    return ConversationHandler.END

# ══════════════════════════════════════════
#              MAIN
# ══════════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"),
        ],
        states={
            REG_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), reg_phone)],
            REG_LEVEL: [CallbackQueryHandler(reg_level, pattern="^lvl_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    absent_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❌ Kelmadim$"), absent_start)],
        states={
            ABSENT_REASON_CHOICE: [CallbackQueryHandler(absent_choice, pattern="^abs_")],
            ABSENT_TEXT: [MessageHandler(filters.ALL & ~filters.COMMAND, absent_text_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    task_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Vazifa yuborish$"), task_start)],
        states={
            TASK_WAIT: [MessageHandler(filters.ALL & ~filters.COMMAND, task_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^adm_broadcast$")],
        states={
            ADMIN_BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    test_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^adm_addtest$")],
        states={
            ADMIN_TEST_LEVEL:    [CallbackQueryHandler(admin_test_level,  pattern="^tst_")],
            ADMIN_TEST_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_test_question)],
            ADMIN_TEST_OPTIONS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_test_options)],
            ADMIN_TEST_ANSWER:   [CallbackQueryHandler(admin_test_answer, pattern="^cor_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ✅ Handler tartibiga e'tibor bering!
    app.add_handler(reg_conv)
    app.add_handler(absent_conv)
    app.add_handler(task_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(test_add_conv)

    # ✅ O'chirish handlerlari — oddiy CallbackQueryHandler (ConversationHandler emas!)
    app.add_handler(CallbackQueryHandler(admin_delete_list,    pattern="^adm_delete$"))
    app.add_handler(CallbackQueryHandler(admin_delete_ask,     pattern="^delstu_"))
    app.add_handler(CallbackQueryHandler(admin_delete_confirm, pattern="^delyes_"))
    app.add_handler(CallbackQueryHandler(noop_callback,        pattern="^noop$"))

    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))
    app.add_handler(CallbackQueryHandler(admin_grade,    pattern="^grd_"))
    app.add_handler(CallbackQueryHandler(admin_done,     pattern="^adm_done$"))
    app.add_handler(CallbackQueryHandler(test_answer,    pattern="^ans_"))
    app.add_handler(MessageHandler(filters.Regex("^✅ Keldim$"),              came))
    app.add_handler(MessageHandler(filters.Regex("^🧪 Test ishlash$"),        test_start))
    app.add_handler(MessageHandler(filters.Regex("^📊 Mening natijalarim$"),  my_results))
    app.add_handler(MessageHandler(filters.Regex("^💻 Mening yo'nalishim$"),  my_level))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Admin panel$"),         admin_panel))
    app.add_handler(CommandHandler("cancel", cancel))

    print(f"💻 IT ta'lim markazi boti ishga tushdi!")
    print(f"👨‍💻 Ustoz: {TEACHER_NAME}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main()