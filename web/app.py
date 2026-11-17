"""
FastAPI Web Admin Dashboard for Kinochi Bot Pro.
Allows browser-based dynamic control over channels, timers, movies, and all bot settings.
"""
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
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

@app.get("/", response_class=HTMLResponse)
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


# ===================== TELEGRAM MINI APP (TMA) =====================

@app.get("/app", response_class=HTMLResponse)
async def serve_miniapp(request: Request):
    """Serve the role-aware Telegram Mini App."""
    return templates.TemplateResponse(
        request=request,
        name="miniapp.html",
        context={"bot_username": settings.BOT_USERNAME}
    )


@app.get("/api/me")
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


@app.get("/api/movies")
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

