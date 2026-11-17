# KINOCHI BOT PRO (ULTIMATE DYNAMIC CINEMA BOT) - REJA

Loyiha: Ultra-zamonaviy, to'liq dinamik (kodga tegmasdan admin paneldan boshqariladigan), taymerli majburiy obunaga ega kino bot.
Joylashuv: `/home/mr-x/Downloads/kinochi_bot`

## 1-Bosqich: Boshlang'ich Tizim va Baza (YAKUNLANGAN)
- [x] 1. Virtual Muhit (venv) va Kerakli Kutubxonalarni O'rnatish (`aiogram 3.x`, `aiosqlite`, `fastapi`, `uvicorn`, `pydantic`, `jinja2`).
- [x] 2. Ma'lumotlar Bazasi va Dinamik Model Tizimi (`database.py`):
    - Foydalanuvchilar (Users, rollar, VIP, cheklovlar)
    - Kanallar / Majburiy Obuna (Kanallar, linklar, taymerlar, zayavka rejimi, faollik)
    - Kinolar va Seriallar (Multi-quality 480p/720p/1080p, janrlar, yillar, reytinglar, fasllar/qismlar)
    - Dinamik Sozlamalar (Settings: shablonlar, start matni, anti-flood, taymerlar, texnik rejim)
    - Promokodlar va VIP tizimi
- [x] 3. Dinamik Majburiy Obuna va Taymer Dvigateli (`services/subscription.py`):
    - Kanallarni tekshirish (get_chat_member, join request)
    - Taymer va oraliq vaqt hisoblash (foydalanuvchiga vaqt berish yoki taymer tugagach bloklash)
    - Dinamik inline tugmalar generatori
- [x] 4. Telegram Admin Panel & FSM Boshqaruv Tizimi (`handlers/admin.py`):
    - Majburiy obunaga kanal qo'shish (link, taymer, nom)
    - Kinolarni qo'shish, tahrirlash, o'chirish
    - Dinamik shablon va start xabarlarini o'zgartirish
    - Xabarnoma yuborish (Broadcast)
    - VIP / Promokodlar va Statistika
    - Baza zaxira nusxasi (Backup)
- [x] 5. Web Admin Dashboard (FastAPI + Modern Dark UI) (`web/`):
    - Brauzerdan turib kanallar, taymerlar va kinolarni qulay boshqarish
    - Statistika grafikalari va jonli monitoring
- [x] 6. Foydalanuvchi Qidiruv va Kino Dvigateli (`handlers/user.py`):
    - Kod orqali qidirish (101, 102...)
    - Nomi bo'yicha qidiruv (fuzzy search)
    - Janrlar va toifalar katalogi
    - Tasodifiy kino va Top kinolar
    - VIP faollashtirish
- [x] 7. Sinov va Tekshiruv (Verification Gate):
    - Avtomatlashtirilgan test skripti (`tests/test_bot_core.py`)
    - Baza, taymerlar, shablonlar va obuna tekshiruvini sinash
- [x] 8. Ishga Tushirish Skripti va To'liq Qo'llanma (`start.sh`, `README.md`, `.env.example`).

## 2-Bosqich: Kengaytirilgan Qo'shimchalar (PRO MAX DARAJA)
- [x] 9. Ma'lumotlar Bazasini Kengaytirish (`database.py`):
    - Referallar tizimi (`referrals` jadvali, ballar, bepul VIP olish)
    - Kino buyurtma qilish tizimi (`movie_requests` jadvali: qidiruvda topilmagan kinoni adminga buyurtma qilish)
    - 5-yulduzli baholash va reyting tizimi (`movie_ratings` jadvali)
    - Yangi dinamik sozlamalar (avto-post, referal mukofotlari, buyurtma matnlari)
- [x] 10. Telegram Inline Mode Dvigateli (`handlers/inline.py`):
    - `@bot_username <kino_nomi>` yozilganda istalgan chatda kino kartalarini chiqarish
    - Bir bosishda do'stlarga kino va kodini yuborish
- [x] 11. Referal va Taklif Dvigateli (`handlers/referral.py`):
    - Har bir userga maxsus taklif linki (`/start ref_USERID`)
    - Referallar balansi, mukofot hisoblash, Top-10 taklifchilar ro'yxati
- [x] 12. "Kino Topilmadi" Buyurtma Qilish Tizimi (`handlers/requests.py`):
    - Kino topilmaganda "📥 Buyurtma berish" tugmasi
    - Admin paneldan va Web paneldan buyurtmalarni ko'rish, qabul qilish va javob yuborish
- [x] 13. Kanalga Avtomatik Post Tashlash Dvigateli (`services/autopost.py`):
    - Yangi kino qo'shilganda dinamik ravishda rasmiy kanalga chiroyli post va "🎬 Kinoni ko'rish" tugmasi bilan tashlash
- [x] 14. Web Dashboardni Yangi Bo'limlar Bilan Kengaytirish (`web/`):
    - `/requests` sahifasi: Foydalanuvchilar buyurtmalarini boshqarish
    - `/referrals` sahifasi: Referallar statistikasi va yetakchilar jadvali
- [x] 15. Kengaytirilgan Sinov va Tekshiruv (Verification Gate):
    - Yangi testlar: inline, referal, buyurtmalar, avto-post
    - Barcha testlar muvaffaqiyatli o'tishini tasdiqlash

## 3-Bosqich: Barcha 12 ta Janr Bo'yicha Kinolar Bazasini To'ldirish (YAKUNLANGAN)
- [x] 16. Telegramga qo'shimcha video fayllarni yuklab, unikal `file_id` larni olish.
- [x] 17. 12 ta asosiy janr (Jangari, Komediya, Fantastika, Qo'rqinchli, Drama, Melodrama, Multfilm, Kriminal, Tarixiy, Detektiv, Anime, Sarguzasht) bo'yicha to'liq ma'lumotlar bazasini yozish (`populate_movies.py`).
- [x] 18. Har bir kino uchun unikal kod (101-112), rasmiy nom, yil, davlat, reyting va tavsiflarni kiritish.
- [x] 19. Baza va kategoriyalarni amalda tekshirish (Verification Gate) — har bir janrda kinolar mavjudligini tasdiqlash.

## 4-Bosqich: Telegram Mini App va Rolli Boshqaruv (Admin vs Foydalanuvchi) hamda Bepul HTTPS Domen (YAKUNLANGAN)
- [x] 20. Bepul HTTPS Domen (Cloudflare Tunnel `cloudflared`) va Render / Local Tunnel yechimini joriy qilish.
- [x] 21. Telegram WebApp JS integratsiyasi (`window.Telegram.WebApp`) va Rolli avto-yo'naltirish (Admin -> Boshqaruv paneli, Foydalanuvchi -> Zamonaviy Kino Katalogi).
- [x] 22. Foydalanuvchilar uchun zamonaviy mobil Web App interfeysi (Netflix/Kinopoisk uslubidagi qora mavzu, jonli qidiruv, janrlar, kinoni 1-bosishda botda ochish/yuklab olish).
- [x] 23. Bot menyusiga doimiy "🎬 Kinolar (Mini App)" tugmasini (`set_chat_menu_button`) ulash.
- [x] 24. Sinov va tekshiruv (Verification Gate) — Admin va Oddiy foydalanuvchi ko'rinishlari, tunnel va API javoblarini tekshirish.
