# -*- coding: utf-8 -*-
import os, re, sys, threading, asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes)
from playwright.sync_api import sync_playwright

# ⬇️ غيّر السطر ده بس
BOT_TOKEN="6506189895:AAHuMhk2nVqU0UDO5fITFFXAyyGM2rC5e-s"
# ⬆️

SITE_URL   = "https://egy.app.spx-learning-square.com/login"
TARGET_URL = "https://egy.app.spx-learning-square.com/subjects/7"

STATE = {
    "running": False,
    "chat_id": None,
    "current_level": 0,
    "current_question": 0,
    "solved": 0,
    "stop_flag": False,
    # بيانات الدخول بتتجمع من المحادثة
    "waiting_for": None,     # "user" أو "pass" أو "answers" أو None
    "user": None,
    "pass": None,
    "answers_text": None,
}

# ================= تحليل الإجابات =================
ORD = {"الاول":1,"الأول":1,"الثاني":2,"الثالث":3,"الرابع":4,"الخامس":5,
       "السادس":6,"السابع":7,"الثامن":8,"التاسع":9,"العاشر":10}
LEVEL_RE = re.compile(r"المستو[ىىي]\s+(?:ال)?(\d+|"+"|".join(ORD)+r")", re.I)
Q_RE = re.compile(r"السؤال\s+(الاول|الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+)", re.I)
ANS_RE = re.compile(r"^\s*الاجابة\s*$")

def norm(s):
    s = re.sub(r"[،,.!?؟؛:\"'«»()\[\]{}]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def parse_answers(text):
    for ar, en in zip("٠١٢٣٤٥٦٧٨٩", "0123456789"):
        text = text.replace(ar, en)
    lines = text.splitlines()
    ans = {}; lvl = 0; i = 0
    while i < len(lines):
        line = lines[i].strip()
        lm = LEVEL_RE.search(line)
        if lm:
            t = lm.group(1)
            lvl = int(t) if t.isdigit() else ORD.get(t, lvl)
        if Q_RE.search(line):
            j = i + 1; q = []
            while j < len(lines) and not ANS_RE.match(lines[j].strip()):
                if Q_RE.search(lines[j]) or LEVEL_RE.search(lines[j]): break
                if lines[j].strip(): q.append(lines[j].strip())
                j += 1
            if j < len(lines) and ANS_RE.match(lines[j].strip()):
                k = j + 1; a = []
                while k < len(lines):
                    s = lines[k].strip()
                    if (not s or Q_RE.search(s) or LEVEL_RE.search(s)):
                        if a: break
                    else:
                        a.append(s)
                    k += 1
                if q and a:
                    ans[(lvl, norm(" ".join(q)))] = " ".join(a)
                i = k; continue
        i += 1
    return ans

def jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)

def find_answer(answers, level, qtext):
    nq = norm(qtext)
    if (level, nq) in answers: return answers[(level, nq)]
    best, best_s = None, 0.0
    for (lv, aq), a in answers.items():
        if lv != level: continue
        s = jaccard(nq, aq)
        if s > best_s: best_s, best = s, a
    return best if best_s >= 0.55 else None

# ================= الإرسال =================
async def notify(app, msg):
    if STATE["chat_id"]:
        try:
            await app.bot.send_message(STATE["chat_id"], msg, parse_mode="HTML")
        except: pass

# ================= محرك الحل =================
def run_solver(app_loop, app, user, pw, answers_text):
    try:
        answers = parse_answers(answers_text)
        asyncio.run_coroutine_threadsafe(
            notify(app, f"✅ تم تحميل {len(answers)} إجابة\n🚀 بدء..."), app_loop)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_context().new_page()
            try:
                page.goto(SITE_URL, wait_until="domcontentloaded")
                page.wait_for_selector("input[type=password]", timeout=60000)
                page.locator("input[type=email], input[type=text], input[type=tel], input[type=number]").first.fill(user)
                page.locator("input[type=password]").first.fill(pw)
                btn = page.locator("button[type=submit], input[type=submit]")
                if btn.count(): btn.first.click()
                else: page.locator("input[type=password]").first.press("Enter")
                page.wait_for_load_state("networkidle"); page.wait_for_timeout(3000)

                if "login" in page.url.lower():
                    asyncio.run_coroutine_threadsafe(
                        notify(app, "❌ فشل الدخول — تأكد من البيانات\nجرب /start تاني"), app_loop)
                    return

                asyncio.run_coroutine_threadsafe(
                    notify(app, "✅ تم تسجيل الدخول"), app_loop)

                page.goto(TARGET_URL, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")

                for lvl in range(1, 23):
                    if STATE["stop_flag"]: break
                    STATE["current_level"] = lvl
                    asyncio.run_coroutine_threadsafe(
                        notify(app, f"📚 المستوى {lvl}/22..."), app_loop)

                    seen = set(); q_count = 0
                    for _ in range(150):
                        if STATE["stop_flag"]: break
                        page.wait_for_timeout(1000)
                        q_el, q_txt = None, None
                        for sel in ("[class*=question]", "[class*=prompt]", "h2", "h3", ".title", "p"):
                            loc = page.locator(sel)
                            for i in range(loc.count()):
                                try: t = (loc.nth(i).inner_text() or "").strip()
                                except: continue
                                if len(t) > 15 and t not in seen:
                                    q_el, q_txt = loc.nth(i), t
                                    break
                            if q_el: break
                        if not q_el: break

                        seen.add(q_txt); q_count += 1
                        STATE["current_question"] = q_count
                        ans = find_answer(answers, lvl, q_txt)
                        if not ans: break

                        clicked = False
                        try:
                            opt = page.locator("label, .option, li, button").filter(has_text=ans.split(" ")[0])
                            if opt.count(): opt.first.click(); clicked = True
                        except: pass
                        if not clicked:
                            try:
                                ta = page.locator("textarea:visible, input[type=text]:visible")
                                if ta.count(): ta.first.fill(ans); clicked = True
                            except: pass
                        if not clicked: break

                        for name in ("Answer", "تحقق", "إجابة", "التالي", "Next"):
                            b = page.get_by_role("button", name=re.compile(name, re.I))
                            if b.count(): b.first.click(); break
                        page.wait_for_timeout(1500)

                    STATE["solved"] += 1
                    asyncio.run_coroutine_threadsafe(
                        notify(app, f"✅ المستوى {lvl} اكتمل ({q_count} سؤال)"), app_loop)

                    nxt = page.get_by_role("button", name=re.compile("التالي|Next|المستوى التالي", re.I))
                    if nxt.count():
                        nxt.first.click(); page.wait_for_timeout(2000)
                    else:
                        break

                asyncio.run_coroutine_threadsafe(
                    notify(app, f"🎉 انتهى! حل {STATE['solved']} مستوى\n/start للبدء من جديد"), app_loop)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    notify(app, f"❌ خطأ: {e}"), app_loop)
            finally:
                browser.close()
    finally:
        STATE["running"] = False

# ================= أوامر البوت =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🚀 تشغيل الحل", callback_data="start")],
        [InlineKeyboardButton("📊 التقدم", callback_data="progress")],
        [InlineKeyboardButton("⏹ إيقاف", callback_data="stop")],
        [InlineKeyboardButton("🔄 تغيير البيانات", callback_data="reset")],
    ]
    await update.message.reply_text(
        "🤖 <b>بوت حل الثقافة المالية</b>\n\n"
        "دوس <b>🚀 تشغيل الحل</b> وهطلب منك:\n"
        "1️⃣ رقمك (المستخدم)\n"
        "2️⃣ الباسورد\n"
        "3️⃣ ملف الإجابات (تلصقه)\n\n"
        "وبعدها يبدأ الحل أوتوماتيك ✨",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML")

async def button_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()

    if q.data == "start":
        if STATE["running"]:
            await q.edit_message_text("⚠️ شغال بالفعل"); return
        # نبدأ عملية جمع البيانات
        STATE["chat_id"] = update.effective_chat.id
        STATE["waiting_for"] = "user"
        STATE["user"] = None
        STATE["pass"] = None
        STATE["answers_text"] = None
        await q.edit_message_text(
            "1️⃣ <b>ابعت رقمك (المستخدم):</b>\n"
            "مثال: <code>123456789</code>",
            parse_mode="HTML")

    elif q.data == "progress":
        await q.edit_message_text(
            f"📊 المستوى: {STATE['current_level']}/22\n"
            f"✅ تم حل: {STATE['solved']}\n"
            f"🔧 {'شغال' if STATE['running'] else 'متوقف'}")

    elif q.data == "stop":
        STATE["stop_flag"] = True
        await q.edit_message_text("⏹ جاري الإيقاف...")

    elif q.data == "reset":
        STATE["user"] = None; STATE["pass"] = None; STATE["answers_text"] = None
        STATE["waiting_for"] = None
        await q.edit_message_text("🔄 تم المسح. /start للبدء من جديد")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يستقبل النصوص اللي يبعتها المستخدم حسب المرحلة"""
    text = update.message.text.strip()
    STATE["chat_id"] = update.effective_chat.id

    if STATE["waiting_for"] == "user":
        STATE["user"] = text
        STATE["waiting_for"] = "pass"
        await update.message.reply_text(
            "2️⃣ <b>ابعت الباسورد:</b>", parse_mode="HTML")
        return

    if STATE["waiting_for"] == "pass":
        STATE["pass"] = text
        STATE["waiting_for"] = "answers"
        await update.message.reply_text(
            "3️⃣ <b>الصق محتوى ملف الإجابات (answers.txt) هنا:</b>\n\n"
            "انسخ كل محتوى الملف والصقه في رسالة واحدة.\n\n"
            "<i>لو مش عارف تجيبه، ممكن أشتغل بالإجابات المدمجة — بس ابعت أي حاجة عشان أبدأ</i>",
            parse_mode="HTML")
        return

    if STATE["waiting_for"] == "answers":
        # لو المستخدم بعت نص طويل = إجابات
        if len(text) < 100:
            # ممكن يكون بيقول حاجة تانية
            await update.message.reply_text(
                "⚠️ النص قصير أوي. الصق محتوى answers.txt كامل، أو ابعت كلمة <code>skip</code> عشان أشتغل بالإجابات المدمجة.",
                parse_mode="HTML")
            return

        STATE["answers_text"] = text
        STATE["waiting_for"] = None

        await update.message.reply_text(
            f"✅ تم استلام كل حاجة!\n"
            f"👤 المستخدم: {STATE['user']}\n"
            f"📚 الإجابات: {len(text)} حرف\n"
            f"🚀 بدء الحل...")

        loop = asyncio.get_running_loop()
        STATE["running"] = True
        STATE["stop_flag"] = False
        STATE["solved"] = 0
        threading.Thread(
            target=run_solver,
            args=(loop, context.application, STATE["user"], STATE["pass"], STATE["answers_text"]),
            daemon=True
        ).start()
        return

    # لو مش في مرحلة معينة
    await update.message.reply_text("ابعت /start عشان تبدأ")

# ================= التشغيل =================
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("🤖 البوت شغال...")
    app.run_polling()
