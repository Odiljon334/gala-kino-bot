# Gala Kino Bot — Production-Grade Telegram Cinema & Streaming Framework

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Aiogram Version](https://img.shields.io/badge/aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)
[![Docker Ready](https://img.shields.io/badge/docker-compose-ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A high-performance, fully asynchronous media distribution and catalog engine for Telegram, featuring zero-code runtime administrative controls, timed forced-subscription gateways, multi-resolution streaming selection, episodic series navigation, and a built-in FastAPI management dashboard.

Engineered from first principles with **Python 3**, **Aiogram 3**, and **SQLite/aiosqlite**, with strict non-blocking I/O and self-healing cloud keep-alive mechanisms.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Telegram Cloud Platform   |
                      +--------------+--------------+
                                     |
                         HTTPS Long-Polling / Webhook
                                     |
                      +--------------v--------------+
                      |       Gala Kino Core        |
                      |   (Aiogram 3 Dispatcher)    |
                      +-------+--------------+------+
                              |              |
              +---------------+              +---------------+
              |                                              |
+-------------v---------------+              +---------------v-------------+
|    Dynamic Middleware &     |              |     FastAPI Admin Portal    |
|   Subscription Gatekeeper   |              |    (Port 8080 - REST/Web)   |
+-------------+---------------+              +---------------+-------------+
              |                                              |
              +---------------+              +---------------+
                              |              |
                      +-------v--------------v------+
                      |      aiosqlite Engine       |
                      |  (Indexed Embedded Storage) |
                      +-----------------------------+
```

---

## Core Capabilities

### 1. Zero-Code Runtime Management
All system parameters—including welcome banners, dynamic caption templates, anti-flood throttling thresholds, and payment coordinates—can be updated in real time via the Telegram admin command suite or the browser-based dashboard without restarting the service.

### 2. Timed Access & Force-Subscription Gatekeeper
- **Channel Verification**: Seamless validation of channel memberships via Telegram Bot API protocols.
- **Configurable Grace Period**: Support for strict instant gating, timed free-preview countdowns (e.g., 30s/60s), or global bypass.
- **Join-Request Friendly**: Fully compatible with public usernames, invite links, and join-request private channels.

### 3. Episodic Series & Multi-Quality Media Router
- **Multi-Resolution Video Delivery**: Dynamic resolution chips (`1080p FHD`, `720p HD`, `480p SD`) delivered through indexed file identifiers.
- **Interactive Player Controls**: Season selector grids alongside cursor-based adjacent playback navigation (`[Previous]`, `[All Episodes]`, `[Next]`).
- **Official Trailer Linking**: Integrated one-tap preview buttons directing users to verified trailers.

### 4. Search & Discovery Engine
- **Unique Code Indexing**: Instant sub-second retrieval by unique content ID.
- **Fuzzy Title Search**: Fast substring and keyword matching across titles, genres, and metadata.
- **Era & Genre Filtering**: Paginated browsing across 12 standard genres and decade-based release ranges (e.g., 2024, 2023, 2020-2022, Vintage).
- **Native Inline Mode**: Query and share catalog items inside any Telegram group or private dialogue via `@bot_username <query>`.

### 5. Cloud Anti-Sleep & Resilient Keep-Alive Daemon
- **Self-Ping Heartbeat**: Built-in background daemon (`services/keepalive.py`) automatically targets `/health` and `/ping` probes every 8 minutes.
- **Zero Cold-Starts**: Prevents cloud hosting providers (e.g., Render, Koyeb) from triggering idle container sleep states.
- **Exponential Reconnect**: The main polling loop automatically re-establishes connections upon transient socket drops or Telegram gateway timeouts.

### 6. User Retention, VIP & Monetization
- **Personal Watchlist**: Integrated native favorites management (`Favorites` toggle on all content cards).
- **5-Star Community Ratings**: Dynamic IMDb-scaled (1-10) scoring calculation per item.
- **Referral Rewards**: Auto-generated deep-links (`/start ref_ID`) rewarding referrers with VIP access points.
- **Automated Content Syndication**: Real-time broadcast of new additions to official Telegram broadcast channels.

---

## Quickstart & Deployment

### Prerequisites
- Python 3.11, 3.12, or 3.13
- A verified Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Linux / macOS / Windows / Docker

---

### Method A: Docker Compose (Production Standard)

1. Clone the repository:
   ```bash
   git clone https://github.com/Odiljon334/gala-kino-bot.git
   cd gala-kino-bot
   ```

2. Create and populate your `.env` configuration:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Launch via Docker Compose:
   ```bash
   docker compose up -d --build
   ```

4. View service telemetry:
   ```bash
   docker compose logs -f
   ```

---

### Method B: Native Linux Systemd Daemon (24/7 Always-On)

1. Set up the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. Configure systemd unit:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp galakinobot.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now galakinobot.service
   ```

3. Inspect daemon status:
   ```bash
   systemctl --user status galakinobot.service
   ```

---

### Method C: One-Click Cloud Deployment (Render.com)

This repository includes a native `render.yaml` infrastructure specification.
1. Fork or push this repository to your GitHub account.
2. In the Render Dashboard, create a **New Blueprint Instance**.
3. Select this repository; Render will automatically scaffold the web service, environment schema, and health probes.

---

## Configuration Reference

Key variables configurable via `.env`:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | `string` | *Required* | Telegram Bot API Token issued by @BotFather |
| `BOT_USERNAME` | `string` | `galakinobot` | Bot handle without the `@` prefix |
| `ADMIN_IDS` | `string` | *Required* | Comma-delimited list of Telegram User IDs with root administrative authority |
| `DATABASE_PATH` | `string` | `kinochi.db` | Local persistent SQLite database storage path |
| `WEB_HOST` | `string` | `0.0.0.0` | Binding host address for FastAPI dashboard |
| `WEB_PORT` | `integer` | `8080` | Binding listening port for FastAPI dashboard |
| `WEB_ADMIN_USERNAME` | `string` | `admin` | HTTP basic auth username for dashboard |
| `WEB_ADMIN_PASSWORD` | `string` | `kinochi2026` | HTTP basic auth password for dashboard |
| `DEFAULT_DAILY_LIMIT` | `integer` | `10` | Daily video delivery quota for non-VIP accounts (0 = infinite) |
| `RENDER_EXTERNAL_URL` | `string` | `""` | Public hostname used by internal anti-sleep self-ping daemon |

---

## Monitoring & Health Probes

The integrated web server exposes endpoints for status monitoring:

- **Health Probe**: `GET /health` (Returns JSON status, service identifier, and UTC timestamp)
- **Ping Probe**: `GET /ping` (Returns lightweight plain-text `pong`)
- **Web Dashboard**: `GET /` (Modern responsive administrative control center)
- **JSON Telemetry**: `GET /api/admin/stats` (Aggregated metrics on users, downloads, views, and catalogs)

Example health check invocation:
```bash
curl -I http://localhost:8080/health
# HTTP/1.1 200 OK
# content-type: application/json
```

---

## Verification & Testing Suite

Execute the comprehensive automated test suite to validate all 13 departmental engines:

```bash
PYTHONPATH=. ./venv/bin/python tests/test_bot_core.py
```

Test coverage includes:
- Dynamic settings persistence and hot-reloading
- Forced-subscription timer calculation algorithms
- Catalog search, multi-quality lookup, and era queries
- Series season indexing and adjacent cursor navigation
- Anti-sleep keep-alive URL resolution and ping response
- VIP lifecycle, token redemptions, and referral balances
- FastAPI administrative route authorization

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
Distributed as free, open-source software for community use.
