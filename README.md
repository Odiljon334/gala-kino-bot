# 🎬 GALA KINO BOT (Ultimate Dynamic Cinema Bot)

> **Eng yuqori darajada moslashuvchan, parametrlari keng, to'liq dinamik boshqariladigan (kodga tegmasdan ishlaydigan) Kinochi Telegram Bot va Zamonaviy Web Admin Dashboard.**

---

## 🌟 Asosiy Xususiyatlari va Afzalliklari

Siz dastur kodini biror marta ham ochishingiz shart emas! Har bir narsa **Telegram Admin Paneli** (`/admin`) yoki **Web Admin Dashboard** brauzer interfeysi orqali dinamik boshqariladi.

### 1. 📢 100% Dinamik Majburiy Obuna va Taymer Tizimi
- **Kanal qo'shish**: Faqatgina havola (link) tashlaysiz, taymerni qo'yasiz — bot uni darhol majburiy obunaga ulaydi!
- **Taymer sozlamasi**:
  - `0 soniya` — Darhol majburiy obuna (kanalga a'zo bo'lmaguncha kino chiqmaydi).
  - `N soniya` (masalan 30 yoki 60 soniya) — Foydalanuvchiga vaqt beriladi, taymer tugagach yoki kanalga a'zo bo'lgach kino ochiladi.
  - Jonli taymer tugmasi: `⏳ Taymer: 45 soniya qoldi`.
- **Global rejimlar**:
  - `STRICT` — Qat'iy majburiy obuna.
  - `TIMER` — Taymerli oraliq obuna.
  - `DISABLED` — Barcha majburiy obunalarni bir zumda to'xtatish.
- **Zayavka (Join Request) va Havolalar**: Bot ommaviy, yopiq kanallarni va tashqi homiy havolalarini avtomatik qo'llab-quvvatlaydi.

### 2. 🤖 Telegram Inline Rejimi (Har qanday chatda qidirish)
- Istalgan chat yoki guruhda `@bot_username <kino_nomi>` deb yozishingiz bilan bot kinolar ro'yxatini chiqarib beradi!
- Bir bosish bilan do'stlarga kino kartasini, reytingini va kodini yuborish imkoni.

### 3. 👥 Referal Tizimi (Do'stlarni taklif qilib bepul VIP olish)
- Har bir foydalanuvchiga shaxsiy taklif havolasi (`t.me/bot?start=ref_USERID`).
- Do'st qo'shilganda avtomatik bepul yuklash balansi beriladi.
- 5 ta do'st taklif qilinsa, avtomatik ravishda 7 kunlik VIP status beriladi (admindan o'zgartiriladi).
- **Top taklif qiluvchilar jadvali** (Leaderboard).

### 4. 📥 "Kino Topilmadi" — Buyurtma Qilish Tizimi
- Foydalanuvchi qidirgan kino bazada bo'lmasa, bir tugma bilan adminga buyurtma berishi mumkin (`📥 Ushbu kinoni buyurtma qilish`).
- Admin panelga va Web dashboardga bildirishnoma tushadi.
- Admin kinoni qo'shgach, `✅ Qo'shildi deb xabar yuborish` tugmasini bosadi va foydalanuvchiga avtomatik xushxabar boradi!

### 5. 📢 Kanalga Avtomatik Post Tashlash (Auto-Posting)
- Yangi kino qo'shilganda, bot avtomatik ravishda rasmiy Telegram kanaliga go'zal post tayyorlab, posteri va `[ 🎬 Kinoni Botda Ko'rish ]` tugmasi bilan tashlab beradi.
- Kanal nomini admindan bir soniyada o'zgartirish yoki yoqish/o'chirish mumkin.

### 6. ⭐ 5-Yulduzli Interaktiv Baholash Tizimi
- Foydalanuvchilar har bir kinoga 1 dan 5 gacha yulduz bera olishadi (`⭐ 1`, `⭐ 2`, `⭐ 3`, `⭐ 4`, `⭐ 5`).
- Bot jamoaviy reytingni avtomatik hisoblab, kino kartochkasidagi ballni yangilab boradi.

### 7. 🎬 Kinolar va Seriallar Boshqaruvi
- **Unikal kod orqali qidiruv**: Masalan `101`, `102` yoki `AVATAR2`.
- **Nomi bo'yicha qidirish**: Aqlli fuzzy qidiruv (masalan: "Forsaj", "Qashqirlar", "O'rgimchak odam").
- **Multi-Quality**: 480p, 720p, 1080p sifatlar.
- **Janrlar va Yillar katalogi**: 12+ janrlar bo'yicha tartiblangan katalog.
- **Seriallar va fasllar**: Har bir fasl va qismlar uchun alohida videolar.
- **Tasodifiy kino ("🎲 Bugun nima ko'rsam?")** va **🏆 Top-10 eng ko'p ko'rilgan kinolar**.

### 8. 🎨 Dinamik Xabar Shabloni (Caption Template)
Bot kodini ochmasdan, admin paneldan turib kino tagiga chiqadigan matn shablonini o'zgartirishingiz mumkin:
```text
🎬 {title} ({year})
🎭 Janr: {genres}
🌐 Davlati: {country}
🔊 Tili: {language}
⭐ Reyting: {rating}/10
⏱ Davomiyligi: {duration}

📝 Tavsif: {description}

🔢 Kodi: {code}
🤖 Botimiz: @{bot_username}
```

### 9. 🌐 Ikkita Boshqaruv Interfeysi (Telegram Panel + Web Dashboard)
1. **Telegram Admin Panel (`/admin`)**:
   - Inline tugmalar, FSM qadamma-qadam so'rovlar, to'liq avtomatlashtirilgan.
2. **Zamonaviy Web Admin Dashboard (FastAPI + Dark Glassmorphism UI)**:
   - Brauzeringizda `http://localhost:8080` manzilida ochiladi.
   - Kanallarni, taymerlarni, kinolarni ko'rish, o'chirish va yangi qo'shish.
   - **Buyurtmalar bo'limi** (`/requests`) va **Referallar bo'limi** (`/referrals`).
   - Real vaqtdagi statistikalar, foydalanuvchilar soni va yuklashlar grafigi.

### 10. 💎 VIP & Monetizatsiya Tizimi
- Bepul foydalanuvchilar uchun kunlik yuklash limiti (masalan kuniga 10 ta kino, admindan o'zgartiriladi).
- Promokodlar generatori (masalan `PREMYERA2026`, 50 kishiga 30 kunlik VIP).
- VIP egalari uchun majburiy obunasiz va cheksiz yuklab olish imkoni.

### 11. 🛡 Anti-Flood, Texnik Ishlar va Backup
- **Texnik ishlar rejimi (Maintenance Mode)**: Bir bosishda botni profilaktikaga olish va foydalanuvchilarga chiroyli xabar chiqarish.
- **Anti-flood**: Botni serverni toliqtiruvchi spam so'rovlardan avtomatik himoyalash.
- **Zaxira nusxasi (Backup)**: Adminga to'g'ridan-to'g'ri Telegram orqali `kinochi.db` bazasini yuborish.

### 12. 🎬 To'liq Seriallar Dvigateli va Yillar Bo'yicha Filtr
- **Fasllar va Qismlar Navigatori**: Seriallar uchun fasl tanlash, qismlar katakchasi va `[⏮ Oldingi qism]`, `[📑 Qismlar]`, `[Keyingi qism ⏭]` interaktiv pleyeri.
- **Yillar va Davrlar Bo'yicha Saralash**: `2024-yil`, `2023-yil`, `2022-yil`, `2020-2021`, `2010-2019`, `Retro (< 2000)` davrlari bo'yicha sahifalash.
- **Treylerlar**: Rasmiy YouTube/Telegram treyler havolalarini kinoga biriktirish.

### 13. 💓 Anti-Sleep 24/7 Always-On Dvigateli (Never Sleep)
- **Render.com / Bepul Bulut Himoyasi**: Bepul bulut serverlarining 15 daqiqalik uyqu rejimiga (Sleep mode) tushib qolishini yo'qotuvchi ichki Self-Ping Heartbeat xizmati (`services/keepalive.py`).
- **Resilient Polling**: Tarmoq uzilganda yoki Telegram taymout berganida 2 soniyada avtomatik qayta ulanuvchi xavfsiz aylana.
- **Healthcheck Probes**: `/health` (JSON) va `/ping` (Text) orqali UptimeRobot yoki istalgan pinger bilan 100% 0-sleep kafolati.

---

## 🚀 Ishga Tushirish (O'rnatish)

### 1. Papkaga o'tish:
```bash
cd /home/mr-x/Downloads/kinochi_bot
```

### 2. Sozlamalarni kiritish:
`.env` faylini ochib, bot tokeningiz va Telegram ID raqamingizni yozing:
```bash
nano .env
```
Misol:
```env
BOT_TOKEN=123456789:AAEkxYz...
BOT_USERNAME=galakinobot
ADMIN_IDS=8430493961
```

### 3. Bir tugma bilan ishga tushirish:
```bash
./start.sh
```
Yoki Linux kompyuterida 24/7 orqa fonda to'xtovsiz ishlatish uchun:
```bash
./start_persistent.sh
```

### 4. Linux Systemd 24/7 Avto-Start (Kompyuter yonganda o'zi ishga tushishi uchun):
```bash
mkdir -p ~/.config/systemd/user
cp galakinobot.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now galakinobot.service
```

- **Telegram Bot**: Polling rejimida darhol javob berishni boshlaydi.
- **Web Dashboard**: Brauzerda oching: `http://localhost:8080` (Login: `admin`, Parol: `kinochi2026`).

---

## 🧪 Avtomatlashtirilgan Sinov (Verification)

Tizimning barcha 13 ta moduli (baza, kanallar, taymerlar, kinolar, seriallar, yillar filtri, inline qidiruv, referallar, buyurtmalar, reytinglar, sevimlilar, anti-sleep keepalive va web dashboard) 100% test qilingan:
```bash
PYTHONPATH=. ./venv/bin/python tests/test_bot_core.py
```
