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

## 5-Bosqich: GALA KINO PRO MAX — Professional Darajadagi Kengaytmalar (YAKUNLANGAN)
- [x] 25. Mini App Pro Max UI: Native Haptic Feedback, Sevimlilar (Favorites/Watchlist ❤️), Treyler ko'rish (🎬), va Premyeralar karuseli.
- [x] 26. Multi-Quality (480p / 720p / 1080p) va Seriallar (Fasllar / Qismlar) tanlash dvigatelini to'liq ulash.
- [x] 27. VIP To'lov va Chek qabul qilish tizimi (`handlers/payment.py`): Chek yuborish, adminga tasdiqlash tugmasi bilan borishi va avtomatik VIP yoqilishi.
- [x] 28. Avtomatik Tizim Zaxirasi (DB Backup) va Kengaytirilgan Xabarnoma (Broadcast Engine).
- [x] 29. Barcha namunaviy videolarni bazadan tozalash (0 ta qoldirish).

## 6-Bosqich: Elita Professional Imkoniyatlar va GitHub Sinxronizatsiyasi
- [x] 30. Telegram Admin panelida Karta raqami (`payment_card_number`), Admin kontakt (`admin_contact`) va VIP narxlarini dinamik o'zgartirish tugmalarini qo'shish.
- [x] 31. Mini App UI: "💎 VIP Obuna" modal oynasi, kartani 1-bosishda nusxalash (`copy to clipboard`), va "❤️ Sevimlilar" (Watchlist) funksiyasini ulash.
- [x] 32. Mini App: Kinoni do'stlarga ulashish ("📤 Ulashish") va kino kodini 1-bosishda nusxalash imkoniyati.
- [x] 33. Avtomatlashtirilgan testlar to'plamini yangilash va verification gate (barcha testlarni 100% muvaffaqiyatli o'tkazish).
- [x] 34. Git repository'ni barcha yangilanishlar bilan GitHub'ga (`git@github.com:Odiljon334/gala-kino-bot.git`) push qilish.

## 7-Bosqich: Mini App Barqarorligi (Auto-Healing Tunnel) va Elita UI/UX Kengaytmalari
- [x] 35. Mini App URL dvigatelini to'liq dinamik qilish (`get_web_app_url()` SQLite + .env real-time integratsiya, statik keshlanishni bartaraf etish).
- [x] 36. Tunnel Auto-Heal & Watchdog dvigateli: tunnel uzilib qolganda avtomatik qayta ulanish, Telegram menyusini yangilash va Error 1033 ni yo'qotish.
- [x] 37. Mini App UI Elita Yangilanishlari:
    - Hashamatli Dark Toast xabarnomalar (standart alert o'rniga zamonaviy animatsiyali bildirishnomalar).
    - 🎲 "Omadli Kino" (Random movie roulette) tugmasi va tezkor tavsiya.
    - 🎬 Sifat tanlash (1080p, 720p, 480p) va Treyler tugmasi.
    - 📢 Mini App ichida Adminlar uchun Majburiy Obuna kanallarini boshqarish paneli.
- [x] 38. Barcha o'zgarishlarni integratsion testdan o'tkazish (Verification Gate).
- [x] 39. Kodlarni GitHub'ga push qilish va bepul doimiy (permanent) serverga ulash qo'llanmasini taqdim etish.

## 8-Bosqich: Mini Appni Butunlay O'chirish va Telegram Nativ Imkoniyatlarini Maksimal Kuchaytirish
- [x] 40. Mini App va Tunnel tizimini butunlay o'chirish:
    - Telegram Menu Button'ni standart holatga qaytarish (`MenuButtonDefault()`).
    - Asosiy klaviaturadan `📱 Gala Kino (Mini App)` va `/app` buyrug'ini olib tashlash.
    - `main.py` dan `tunnel_watchdog` ni to'xtatish va chiqarib tashlash.
- [x] 41. Baza va Sevimlilar (Watchlist) Nativ Tizimi (`database.py`):
    - `user_favorites` jadvali va funksiyalari (`add_favorite`, `remove_favorite`, `get_user_favorites`, `is_favorite`).
    - Asosiy menyuga `❤️ Sevimlilarim` tugmasini kiritish va boshqarish interfeysi.
- [x] 42. Telegram Kino Kartasi va Multi-Quality Nativ Dvigateli:
    - Har bir kino kartasiga `[❤️ Sevimlilarga qo'shish / o'chirish]` inline tugmasi.
    - Ko'p sifatli kinolar uchun nativ sifat tugmalari (`[🎬 1080p]`, `[🎬 720p]`, `[🎬 480p]`).
    - Do'stlarga 1-bosishda ulashish tugmasi (`switch_inline_query`).
- [x] 43. Janrlar va Top-10 Kinolar uchun Interaktiv Sahifalash (Pagination):
    - 12 ta janr bo'yicha kinolarni sahifama-sahifa (`◀️`, `▶️`) ko'rish.
    - Nativ Telegram inline menyularini yanada tezkor va jozibador qilish.
- [x] 44. Avtomatlashtirilgan testlar to'plamini yangilash va verification gate (100% muvaffaqiyatli).
- [x] 45. GitHub repozitoriyasiga to'liq yuklash va yangilangan botni ishga tushirish.

## 9-Bosqich: GALA KINO ULTIMATE POWER PACK (Maksimal Kuchaytirish) (YAKUNLANGAN)
- [x] 46. Seriallar (Fasllar va Qismlar) Dvigatelini To'liq Ulanishi:
    - Baza: `get_episodes_by_season`, `get_movie_seasons`, `get_adjacent_episodes`, `get_episode_by_id`.
    - Telegram: Serial ochilganda Fasllar tanlash, Qismlar tugmalari (`[1-qism]`, `[2-qism]...`), va qism ko'rilganda `[⏮ Oldingi]`, `[Keyingi ⏭]` navigatsiyasi.
    - Admin: Telegram paneldan turib serial qismlarini (`add_ep_start`) birma-bir video va nomi bilan qo'shish.
- [x] 47. Yillar Bo'yicha Qidiruv va Filtr Dvigateli (`database.py` & `handlers/user.py`):
    - `get_movies_by_year_range(start_year, end_year, limit, offset)`.
    - Janrlar menyusida `📅 Yillar bo'yicha saralash` (`2024`, `2023`, `2022`, `2020-2021`, `2010-2019`, `Retro`) va interaktiv sahifalash (`◀️`, `▶️`).
- [x] 48. Treyler Ko'rish Tizimi:
    - Kinoda `trailer_url` bo'lganda `[🎬 Rasmiy Treyler]` inline tugmasi va preview.
    - Admin paneldan istalgan kinoga treyler YouTube/Telegram havolasini biriktirish (`set_trailer_start`).
- [x] 49. Telegram Inline Rejimini Pro Darajaga Ko'tarish (`handlers/inline.py`):
    - Bo'sh qidiruvda (`@galakinobot `) avtomatik ravishda eng ommabop Top-10 kinolar kartalarini chiqarish.
    - Qidiruv natijalaridan to'g'ridan-to'g'ri botga havola va do'stlarga yuborish tugmasi.
- [x] 50. Avtomatlashtirilgan testlar to'plamini kengaytirish va verification gate (12 ta test 100% muvaffaqiyatli).
- [x] 51. Yangilanishlarni GitHub repozitoriyasiga push qilish va botni qayta ishga tushirish.

## 10-Bosqich: ANTI-SLEEP ENGINE & 24/7 ALWAYS-ON RESILIENCE (Uxlab Qolishni Yo'qotish) (YAKUNLANGAN)
- [x] 52. Web Server Health & Keep-Alive Endpoints (`web/app.py`):
    - `GET /health` (JSON status, uptime, service info, 200 OK)
    - `GET /ping` (Plain text 'pong')
- [x] 53. Anti-Sleep Heartbeat Daemon (`services/keepalive.py`):
    - Har 8 daqiqada (480s) `RENDER_EXTERNAL_URL`, `KEEPALIVE_URL` yoki bazadagi `keepalive_url` ga HTTP self-ping yuborish.
    - Render'ning 15 daqiqalik nofaollik taymerini nollab, uxlatib qo'ymaslik (Never Sleep).
- [x] 54. Resilient Telegram Polling Loop & Auto-Reconnect (`main.py`):
    - `dp.start_polling` ni auto-recovery `while True` loop va backoff bilan o'rash.
    - Tarmoq uzilishi yoki Telegram taymoutlarida bot to'xtab qolmasdan darhol qayta ulanishi.
- [x] 55. Dinamik Sozlamalar va Admin Diagnostikasi (`database.py` & `handlers/admin.py`):
    - `keepalive_url` va `keepalive_interval` parametrlarini qo'shish.
    - Telegram Admin va Web paneldan Anti-Sleep URL ni o'rnatish va holatini ko'rish.
- [x] 56. Lokal Linux Uchun 24/7 Doimiy Systemd Xizmati (`galakinobot.service` & `start_persistent.sh`):
    - Kompyuter o'chib yonganda yoki bot yiqilganda avtomatik qayta ishga tushiruvchi systemd skripti.
- [x] 57. Avtomatlashtirilgan Testlar va Verification Gate:
    - `/health`, `/ping` va keepalive funksiyalari uchun testlar yozish va 100% muvaffaqiyatli o'tkazish (13/13 test OK).
- [x] 58. GitHub repozitoriyasiga push qilish va Render'ga yangilanishni yetkazish.
