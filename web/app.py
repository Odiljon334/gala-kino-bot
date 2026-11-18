"""
FastAPI Web Admin Dashboard for Kinochi Bot Pro.
Allows browser-based dynamic control over channels, timers, movies, and all bot settings.
"""
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from database import (
    get_system_stats,
    get_all_settings,
    set_setting,
    get_all_channels,
    add_channel,
    delete_channel,
    toggle_channel_status,
    get_all_movies,
    add_movie,
    delete_movie,
    get_all_movie_requests,
    update_movie_request_status,
    get_top_referrers
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Gala Kino Web Dashboard")

# Mount static and templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ===================== ROUTES =====================

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Ultra-lightweight health-check endpoint for Uptime monitoring & Keep-Alive pings."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Gala Kino Bot Pro",
        "bot": settings.BOT_USERNAME
    })

@app.api_route("/ping", methods=["GET", "HEAD"])
async def ping_check():
    """Simple ping-pong probe for keep-alive and curl checks."""
    return PlainTextResponse("pong")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def dashboard_home(request: Request):
    stats = await get_system_stats()
    settings_dict = await get_all_settings()
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"stats": stats, "settings_dict": settings_dict}
    )


# --- CHANNELS & TIMERS ---

@app.get("/channels", response_class=HTMLResponse)
async def view_channels(request: Request):
    channels = await get_all_channels()
    settings_dict = await get_all_settings()
    return templates.TemplateResponse(
        request=request,
        name="channels.html",
        context={"channels": channels, "settings_dict": settings_dict}
    )


@app.post("/channels/add")
async def handle_add_channel(
    invite_link: str = Form(...),
    title: str = Form(...),
    channel_id: str = Form(None),
    timer_seconds: int = Form(0)
):
    clean_ch_id = channel_id.strip() if channel_id and channel_id.strip() else None
    await add_channel(
        title=title.strip(),
        invite_link=invite_link.strip(),
        channel_id=clean_ch_id,
        button_text=title.strip(),
        timer_seconds=timer_seconds,
        is_active=1
    )
    return RedirectResponse(url="/channels", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/channels/toggle/{channel_id}")
async def handle_toggle_channel(channel_id: int):
    await toggle_channel_status(channel_id)
    return RedirectResponse(url="/channels", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/channels/delete/{channel_id}")
async def handle_delete_channel(channel_id: int):
    await delete_channel(channel_id)
    return RedirectResponse(url="/channels", status_code=status.HTTP_303_SEE_OTHER)


# --- MOVIES ---

@app.get("/movies", response_class=HTMLResponse)
async def view_movies(request: Request):
    movies = await get_all_movies(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="movies.html",
        context={"movies": movies}
    )


@app.post("/movies/add")
async def handle_add_movie(
    code: str = Form(...),
    title: str = Form(...),
    year: int = Form(2024),
    country: str = Form("AQSH"),
    genres: str = Form("Kino"),
    language: str = Form("O'zbek tilida"),
    quality_720_file_id: str = Form(...),
    rating: float = Form(7.5),
    description: str = Form("")
):
    movie_dict = {
        "code": code.strip().upper(),
        "title": title.strip(),
        "year": year,
        "country": country.strip(),
        "genres": genres.strip(),
        "language": language.strip(),
        "quality_720_file_id": quality_720_file_id.strip(),
        "rating": rating,
        "description": description.strip() if description.strip() else "Ajoyib kino tomosha qiling.",
        "duration": "1 soat 45 daqiqa"
    }
    await add_movie(movie_dict)
    return RedirectResponse(url="/movies", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/movies/delete/{movie_id}")
async def handle_delete_movie(movie_id: int):
    await delete_movie(movie_id)
    return RedirectResponse(url="/movies", status_code=status.HTTP_303_SEE_OTHER)


# --- MOVIE REQUESTS ---

@app.get("/requests", response_class=HTMLResponse)
async def view_requests(request: Request):
    requests_list = await get_all_movie_requests(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="requests.html",
        context={"requests_list": requests_list}
    )


@app.post("/requests/{req_id}/complete")
async def handle_complete_request(req_id: int):
    await update_movie_request_status(req_id, "completed", "Web paneldan tasdiqlandi")
    return RedirectResponse(url="/requests", status_code=status.HTTP_303_SEE_OTHER)


# --- REFERRALS ---

@app.get("/referrals", response_class=HTMLResponse)
async def view_referrals(request: Request):
    top_list = await get_top_referrers(limit=25)
    settings_dict = await get_all_settings()
    return templates.TemplateResponse(
        request=request,
        name="referrals.html",
        context={"top_referrers": top_list, "settings_dict": settings_dict}
    )


# --- DYNAMIC SETTINGS ---

@app.get("/settings", response_class=HTMLResponse)
async def view_settings(request: Request):
    settings_dict = await get_all_settings()
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"settings_dict": settings_dict}
    )


@app.post("/settings/save")
async def handle_save_settings(request: Request):
    form_data = await request.form()
    for key, value in form_data.items():
        if isinstance(value, str):
            await set_setting(key, value.strip())
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)


# ===================== WEB DASHBOARD =====================

@app.get("/app")
async def redirect_app():
    return RedirectResponse(url="/", status_code=302)


@app.api_route("/api/me", methods=["GET", "HEAD"])
async def api_me(user_id: int = 0):
    """Check user identity and role (Admin vs Regular User)."""
    is_admin = user_id in settings.ADMIN_IDS
    from database import get_user
    user = await get_user(user_id) if user_id else None
    return {
        "user_id": user_id,
        "is_admin": is_admin,
        "user": user,
        "bot_username": settings.BOT_USERNAME
    }


@app.api_route("/api/vip_info", methods=["GET", "HEAD"])
async def api_vip_info():
    """Get VIP pricing and payment card credentials."""
    from database import get_setting
    card = await get_setting("payment_card_number", "8600 •••• •••• 1234 (Odiljon N.)")
    contact = await get_setting("admin_contact", "@Odiljon_n3")
    return {
        "card_number": card,
        "admin_contact": contact,
        "prices": [
            {"period": "1 oy", "price": "15,000 so'm"},
            {"period": "3 oy", "price": "35,000 so'm"},
            {"period": "1 yil", "price": "99,000 so'm"}
        ]
    }


@app.api_route("/api/movies", methods=["GET", "HEAD"])
async def api_movies(q: str = "", genre: str = ""):
    """Return filtered or full movies catalog."""
    from database import search_movies, get_movies_by_genre
    if q.strip():
        movies = await search_movies(q.strip(), limit=50)
    elif genre.strip() and genre.strip().lower() != "barchasi":
        movies = await get_movies_by_genre(genre.strip(), limit=50)
    else:
        movies = await get_all_movies(limit=100)
    return {"movies": movies}


@app.post("/api/deliver")
async def api_deliver_movie(request: Request):
    """Deliver movie to user directly via Bot API from Mini App."""
    from aiogram import Bot
    from database import get_or_create_user
    from handlers.user import deliver_movie_by_code
    
    data = await request.json()
    user_id = data.get("user_id")
    code = data.get("code", "").strip().upper()
    if not user_id or not code:
        raise HTTPException(status_code=400, detail="user_id va code talab qilinadi")
    
    user = await get_or_create_user(user_id, None, "MiniApp User")
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        class FakeMessage:
            def __init__(self, chat_id):
                self.chat = type("Chat", (), {"id": chat_id})()
            async def answer(self, text, reply_markup=None):
                return await bot.send_message(chat_id=self.chat.id, text=text, reply_markup=reply_markup)
                
        fake_msg = FakeMessage(user_id)
        success = await deliver_movie_by_code(fake_msg, bot, code, user)
        return {"status": "ok" if success else "error"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await bot.session.close()


@app.post("/api/request_movie")
async def api_request_movie(request: Request):
    from database import create_movie_request
    data = await request.json()
    user_id = data.get("user_id", 0)
    user_name = data.get("user_name", "Foydalanuvchi")
    title = data.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Kino nomi kiritilmadi!")
    req_id = await create_movie_request(user_id, user_name, title)
    return {"status": "ok", "request_id": req_id}


@app.get("/api/admin/stats")
async def api_admin_stats(user_id: int = 0):
    if user_id not in settings.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")
    stats = await get_system_stats()
    return {"stats": stats}


@app.post("/api/admin/movies/add_json")
async def api_admin_add_movie(request: Request):
    data = await request.json()
    admin_id = data.get("admin_id", 0)
    if admin_id not in settings.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")
    
    movie_dict = {
        "code": data["code"].strip().upper(),
        "title": data["title"].strip(),
        "year": int(data.get("year", 2024)),
        "country": data.get("country", "AQSH").strip(),
        "genres": data.get("genres", "Kino").strip(),
        "language": data.get("language", "O'zbek tilida").strip(),
        "quality_720_file_id": data.get("file_id", "").strip(),
        "rating": float(data.get("rating", 7.5)),
        "description": data.get("description", "Ajoyib kino tomosha qiling.").strip(),
        "duration": data.get("duration", "1 soat 45 daqiqa").strip()
    }
    await add_movie(movie_dict)
    return {"status": "ok"}


@app.get("/api/admin/channels_json")
async def api_admin_channels(user_id: int = 0):
    if user_id not in settings.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")
    channels = await get_all_channels()
    return {"channels": channels}


@app.post("/api/admin/channels/add_json")
async def api_admin_add_channel(request: Request):
    data = await request.json()
    admin_id = data.get("admin_id", 0)
    if admin_id not in settings.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")
    
    await add_channel(
        title=data["title"].strip(),
        invite_link=data["invite_link"].strip(),
        channel_id=data.get("channel_id"),
        button_text=data["title"].strip(),
        timer_seconds=int(data.get("timer_seconds", 0)),
        is_active=1
    )
    return {"status": "ok"}


@app.post("/api/admin/channels/toggle_json")
async def api_admin_toggle_channel(request: Request):
    data = await request.json()
    admin_id = data.get("admin_id", 0)
    channel_id = data.get("channel_id", 0)
    if admin_id not in settings.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")
    from database import toggle_channel_status
    new_status = await toggle_channel_status(channel_id)
    return {"status": "ok", "new_status": new_status}


