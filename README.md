
# Telegram Playwright Bot 🤖

بوت تيليجرام وأتمتة سحابية مخصصة لأداء المهام وتصفح المواقع باستخدام مكتبة **Playwright**. تم إعداد هذا المشروع ليعمل بسلاسة عبر البيئات السحابية مثل **GitHub Actions** أو منصات الاستضافة المختلفة دون الحاجة إلى تشغيله محلياً على الهاتف.

---

## 🚀 المميزات (Features)

- 🤖 **أتمتة كاملة للمتصفح:** استخدام مكتبة Playwright للتحكم بالمتصفحات والتعامل مع الصفحات الديناميكية.
- 📱 **دعم الأجهزة المحمولة:** يمكن إدارته وتحديثه بسهولة من خلال خوادم السحاب دون التأثر بقيود الهواتف الذكية.
- ⚡ **تكامل مع Telegram:** إرسال التنبيهات والبيانات المستخرجة فوراً عبر التليجرام.

---

## 🛠️ التقنيات المستخدمة (Tech Stack)

- **اللغة:** Python 3.x
- **الأتمتة:** Playwright
- **البوت:** python-telegram-bot

---

## 📦 التثبيت والتشغيل المحلّي (Installation)

> **ملاحظة:** تشغيل Playwright يتطلب بيئة سطح مكتب (Windows / Linux / macOS) ولا يعمل محلياً على تطبيقات الهاتف مثل Pydroid 3.

1. **استคลون المشروع (Clone the repository):**
   ```bash
   git clone [https://github.com/username/repository-name.git](https://github.com/username/repository-name.git)
   cd repository-name

 * إنشاء البيئة الافتراضية وتفعيلها:
   python -m venv venv
# وعلى Linux/macOS:
source venv/bin/activate
# وعلى Windows:
venv\Scripts\activate

 * تثبيت الحزم المطلوبة:
   pip install -r requirements.txt

 * تثبيت محركات المتصفح الخاصة بـ Playwright:
   playwright install

 * تشغيل المشروع:
   python main.py

🌐 التشغيل على السحاب (Cloud Deployment)
1. عبر GitHub Actions (للسكريبتات المجدولة)
تم إعداد المشروع ليعمل عبر GitHub Actions لتنفيذ المهام وسحب البيانات دورياً وبشكل آلي.
2. عبر منصات الاستضافة (Render / Railway)
لتشغيل البوت بشكل مستمر (24/7):
 * قم بربط مستودع GitHub الخاص بك بالمنصة.
 * أضف المتغيرات البيئية (Environment Variables) مثل TELEGRAM_TOKEN.
 * اضبط أمر التشغيل على python main.py.
📋 ملف Requirements (requirements.txt)
تأكد من وجود الملفات التالية في المستودع:
python-telegram-bot
playwright


