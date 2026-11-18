"""
Comprehensive Verification Suite for Kinochi Bot Pro.
Tests database, dynamic settings, subscription timer logic, template rendering,
movie retrieval, promocode activation, and FastAPI web routes.
"""
import os
import asyncio
import unittest
from datetime import datetime

# Setup test database path before imports
os.environ["DATABASE_PATH"] = "/home/mr-x/Downloads/kinochi_bot/test_kinochi.db"
os.environ["BOT_TOKEN"] = "123456789:TEST_BOT_TOKEN_FOR_MOCK"

from database import (
    init_db,
    get_setting,
    set_setting,
    get_all_settings,
    add_channel,
    get_active_channels,
    toggle_channel_status,
    delete_channel,
    add_movie,
    get_movie_by_code,
    get_movie_by_id,
    search_movies,
    get_movies_by_genre,
    get_random_movie,
    add_episode,
    get_episodes_by_movie,
    get_or_create_user,
    set_user_vip,
    check_user_vip_status,
    create_promocode,
    redeem_promocode,
    get_system_stats,
    add_referral,
    get_user_referrals_count,
    get_top_referrers,
    create_movie_request,
    get_all_movie_requests,
    update_movie_request_status,
    rate_movie,
    get_movie_rating_stats
)
from services.subscription import get_or_create_timer_session, build_subscription_keyboard
from services.template import format_caption, format_start_message
from web.app import app
from fastapi.testclient import TestClient


class TestKinochiBotCore(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Initialize fresh test database
        if os.path.exists(os.environ["DATABASE_PATH"]):
            os.remove(os.environ["DATABASE_PATH"])
        await init_db()

    async def asyncTearDown(self):
        if os.path.exists(os.environ["DATABASE_PATH"]):
            os.remove(os.environ["DATABASE_PATH"])

    async def test_01_dynamic_settings(self):
        """Test getting and updating dynamic settings without modifying code."""
        # Check default setting
        bot_name = await get_setting("bot_name")
        self.assertEqual(bot_name, "Gala Kino")

        # Update setting dynamically
        await set_setting("bot_name", "Yangi Super Kino Bot")
        updated_name = await get_setting("bot_name")
        self.assertEqual(updated_name, "Yangi Super Kino Bot")

        # Test maintenance mode toggle
        await set_setting("maintenance_mode", "1")
        self.assertEqual(await get_setting("maintenance_mode"), "1")

    async def test_02_channels_and_timers(self):
        """Test adding channels with timer parameters as requested by user."""
        # User requirement: add channel link, set timer, and it adds to mandatory subscription
        ch1_id = await add_channel(
            title="Premyera Kinolar",
            invite_link="https://t.me/premyera_kino",
            channel_id="-100111222333",
            button_text="➕ 1-Kanalga a'zo bo'lish",
            timer_seconds=45,
            is_active=1
        )
        self.assertGreater(ch1_id, 0)

        # Check active channels list
        active_channels = await get_active_channels()
        self.assertEqual(len(active_channels), 1)
        self.assertEqual(active_channels[0]["timer_seconds"], 45)
        self.assertEqual(active_channels[0]["invite_link"], "https://t.me/premyera_kino")

        # Test Timer Session Calculation
        rem_seconds = await get_or_create_timer_session(
            telegram_id=987654321, 
            channel_id=ch1_id, 
            timer_seconds=45
        )
        self.assertEqual(rem_seconds, 45)

        # Test Keyboard Generator with Timer
        kb = build_subscription_keyboard(active_channels, target_code="101", remaining_seconds=45)
        self.assertTrue(len(kb.inline_keyboard) >= 2)

        # Test Toggle Channel
        new_status = await toggle_channel_status(ch1_id)
        self.assertEqual(new_status, 0)
        self.assertEqual(len(await get_active_channels()), 0)

        # Test Delete Channel
        del_res = await delete_channel(ch1_id)
        self.assertTrue(del_res)

    async def test_03_movies_catalog_and_search(self):
        """Test adding movies, multi-quality file IDs, search by code and title."""
        movie_data = {
            "code": "101",
            "title": "Forsaj 10",
            "original_title": "Fast X",
            "year": 2023,
            "country": "AQSH",
            "genres": "Jangari, Poyga, Kriminal",
            "quality_720_file_id": "BAACAgIAAxkBAA...",
            "rating": 7.8,
            "description": "Dom Toreto va uning oilasi so'nggi dushman bilan kurashadi."
        }
        movie_id = await add_movie(movie_data)
        self.assertGreater(movie_id, 0)

        # Retrieve by code
        movie = await get_movie_by_code("101")
        self.assertIsNotNone(movie)
        self.assertEqual(movie["title"], "Forsaj 10")
        self.assertEqual(movie["year"], 2023)

        # Search by fuzzy query
        results = await search_movies("Forsaj")
        self.assertEqual(len(results), 1)

        # Search by genre
        genre_movies = await get_movies_by_genre("Poyga")
        self.assertEqual(len(genre_movies), 1)

        # Dynamic Caption Rendering
        caption = await format_caption(movie)
        self.assertIn("Forsaj 10", caption)
        self.assertIn("101", caption)
        self.assertIn("Jangari", caption)

    async def test_04_episodes_for_series(self):
        """Test series and episodes management."""
        movie_data = {
            "code": "SER_01",
            "title": "Qashqirlar Makoni",
            "year": 2003,
            "genres": "Kriminal, Drama",
            "is_series": 1
        }
        series_id = await add_movie(movie_data)
        
        # Add episodes
        ep1 = await add_episode(series_id, episode_number=1, file_id="EP_01_FILE_ID", episode_title="1-Qism")
        ep2 = await add_episode(series_id, episode_number=2, file_id="EP_02_FILE_ID", episode_title="2-Qism")
        
        episodes = await get_episodes_by_movie(series_id)
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0]["episode_number"], 1)

    async def test_05_promocodes_and_vip(self):
        """Test promocode generation and redemption."""
        user = await get_or_create_user(telegram_id=555666777, username="test_user", first_name="Ali")
        self.assertFalse(await check_user_vip_status(user))

        # Create promo
        promo_id = await create_promocode(code="YIL2026", duration_days=30, max_uses=2)
        self.assertGreater(promo_id, 0)

        # Redeem promo
        success, msg = await redeem_promocode("YIL2026", 555666777)
        self.assertTrue(success)
        self.assertIn("Tabriklaymiz", msg)

        # Re-check user VIP status
        updated_user = await get_or_create_user(telegram_id=555666777, username="test_user", first_name="Ali")
        self.assertTrue(await check_user_vip_status(updated_user))

    async def test_06_fastapi_web_dashboard(self):
        """Test FastAPI Web Dashboard HTTP endpoints."""
        client = TestClient(app)
        
        # GET / (Home)
        res_home = client.get("/")
        self.assertEqual(res_home.status_code, 200)
        self.assertIn("Gala Kino", res_home.text)

        # GET /channels
        res_ch = client.get("/channels")
        self.assertEqual(res_ch.status_code, 200)
        self.assertIn("Majburiy Obuna", res_ch.text)

        # POST /channels/add
        res_add_ch = client.post(
            "/channels/add",
            data={
                "title": "Web Test Kanal",
                "invite_link": "https://t.me/web_test",
                "channel_id": "-100999888",
                "timer_seconds": 60
            },
            follow_redirects=False
        )
        self.assertEqual(res_add_ch.status_code, 303)

        # Check channel was added
        channels = await get_active_channels()
        self.assertTrue(any(c["title"] == "Web Test Kanal" for c in channels))

        # GET /movies
        res_movies = client.get("/movies")
        self.assertEqual(res_movies.status_code, 200)

        # GET /settings
        res_settings = client.get("/settings")
        self.assertEqual(res_settings.status_code, 200)

        # GET /requests
        res_req = client.get("/requests")
        self.assertEqual(res_req.status_code, 200)
        self.assertIn("Buyurtmalar", res_req.text)

        # GET /referrals
        res_ref = client.get("/referrals")
        self.assertEqual(res_ref.status_code, 200)
        self.assertIn("Referallar", res_ref.text)

    async def test_07_referrals_and_rewards(self):
        """Test user referral tracking and automatic VIP reward thresholds."""
        # Create users
        u1 = await get_or_create_user(telegram_id=1001, username="user_one", first_name="User1")
        u2 = await get_or_create_user(telegram_id=1002, username="user_two", first_name="User2")
        
        # Add referral
        success, msg = await add_referral(referrer_id=1001, referred_id=1002)
        self.assertTrue(success)
        self.assertIn("qo'shildi", msg)

        # Count check
        count = await get_user_referrals_count(1001)
        self.assertEqual(count, 1)

        # Duplicate referral check (should fail)
        dup_success, _ = await add_referral(referrer_id=1001, referred_id=1002)
        self.assertFalse(dup_success)

        # Leaderboard
        top = await get_top_referrers(limit=5)
        self.assertEqual(len(top), 1)
        self.assertEqual(top[0]["telegram_id"], 1001)

    async def test_08_movie_requests_lifecycle(self):
        """Test movie request creation, admin listing, and status completion."""
        req_id = await create_movie_request(
            telegram_id=2001,
            user_name="Jasur",
            movie_title="Gladiator 2"
        )
        self.assertGreater(req_id, 0)

        # Fetch requests
        pending_requests = await get_all_movie_requests(status_filter="pending")
        self.assertTrue(any(r["id"] == req_id for r in pending_requests))

        # Admin completes request
        await update_movie_request_status(req_id, "completed", "Botga yuklandi")
        
        completed_requests = await get_all_movie_requests(status_filter="completed")
        target = next((r for r in completed_requests if r["id"] == req_id), None)
        self.assertIsNotNone(target)
        self.assertEqual(target["status"], "completed")

    async def test_09_movie_rating_calculation(self):
        """Test 5-star user rating system and average score recalculation."""
        movie_id = await add_movie({
            "code": "AVATAR_TEST",
            "title": "Avatar 3",
            "quality_720_file_id": "FILE_AVATAR"
        })

        # User 1 gives 5 stars
        avg1 = await rate_movie(movie_id, telegram_id=3001, stars=5)
        self.assertEqual(avg1, 10.0)

        # User 2 gives 3 stars (avg = 4.0 stars -> 8.0 on 10-scale)
        avg2 = await rate_movie(movie_id, telegram_id=3002, stars=3)
        self.assertEqual(avg2, 8.0)

        stats = await get_movie_rating_stats(movie_id)
        self.assertEqual(stats["total_ratings"], 2)

    async def test_10_user_favorites(self):
        """Test adding, checking, listing and removing user favorites."""
        from database import add_movie, add_favorite, is_favorite, get_user_favorites, remove_favorite
        movie_id = await add_movie({
            "code": "FAV_TEST",
            "title": "Sevimli Kino",
            "quality_720_file_id": "FILE_FAV"
        })
        user_id = 998877
        
        # Add favorite
        added = await add_favorite(user_id, movie_id)
        self.assertTrue(added)
        
        # Check favorite
        fav = await is_favorite(user_id, movie_id)
        self.assertTrue(fav)
        
        # List favorites
        favs = await get_user_favorites(user_id)
        self.assertEqual(len(favs), 1)
        self.assertEqual(favs[0]["id"], movie_id)
        
        # Remove favorite
        removed = await remove_favorite(user_id, movie_id)
        self.assertTrue(removed)
        fav_after = await is_favorite(user_id, movie_id)
        self.assertFalse(fav_after)

    async def test_11_series_and_episodes(self):
        """Test series creation, adding episodes, seasons navigation and adjacent episodes."""
        from database import (
            add_movie, add_episode, get_movie_seasons, get_episodes_by_season,
            get_episode_by_id, get_adjacent_episodes
        )
        series_id = await add_movie({
            "code": "SERIES_TEST",
            "title": "Kurtlar Vadisi",
            "is_series": 1,
            "quality_720_file_id": "SERIES_MAIN_FILE"
        })
        self.assertGreater(series_id, 0)

        # Add Season 1 episodes
        ep1_id = await add_episode(series_id, episode_number=1, file_id="EP_1_FILE", episode_title="Boshlanish", season_number=1)
        ep2_id = await add_episode(series_id, episode_number=2, file_id="EP_2_FILE", episode_title="Tuzoq", season_number=1)
        ep3_id = await add_episode(series_id, episode_number=3, file_id="EP_3_FILE", episode_title="Hujum", season_number=1)

        # Add Season 2 episode
        ep4_id = await add_episode(series_id, episode_number=1, file_id="EP_S2_1_FILE", episode_title="Yangi Davr", season_number=2)

        # Check unique seasons
        seasons = await get_movie_seasons(series_id)
        self.assertEqual(seasons, [1, 2])

        # Check episodes of season 1
        s1_episodes = await get_episodes_by_season(series_id, season_number=1)
        self.assertEqual(len(s1_episodes), 3)
        self.assertEqual(s1_episodes[0]["id"], ep1_id)
        self.assertEqual(s1_episodes[1]["episode_number"], 2)

        # Check single episode retrieval
        ep_data = await get_episode_by_id(ep2_id)
        self.assertIsNotNone(ep_data)
        self.assertEqual(ep_data["episode_title"], "Tuzoq")

        # Check adjacent navigation
        prev_ep, next_ep = await get_adjacent_episodes(series_id, season_number=1, episode_number=2)
        self.assertIsNotNone(prev_ep)
        self.assertEqual(prev_ep["episode_number"], 1)
        self.assertIsNotNone(next_ep)
        self.assertEqual(next_ep["episode_number"], 3)

    async def test_12_movies_by_year_range(self):
        """Test filtering movies by release era / year range with pagination."""
        from database import add_movie, get_movies_by_year_range
        # Add movies across different years
        await add_movie({"code": "YR_2024", "title": "Dune 2", "year": 2024, "quality_720_file_id": "DUNE"})
        await add_movie({"code": "YR_2023", "title": "Oppenheimer", "year": 2023, "quality_720_file_id": "OPP"})
        await add_movie({"code": "YR_2022", "title": "Avatar 2", "year": 2022, "quality_720_file_id": "AV2"})
        await add_movie({"code": "YR_1999", "title": "Matrix", "year": 1999, "quality_720_file_id": "MTX"})

        # Query 2024
        movies_2024 = await get_movies_by_year_range(2024, 2024, limit=5, offset=0)
        self.assertEqual(len(movies_2024), 1)
        self.assertEqual(movies_2024[0]["code"], "YR_2024")

        # Query 2022-2023
        movies_recent = await get_movies_by_year_range(2022, 2023, limit=5, offset=0)
        self.assertEqual(len(movies_recent), 2)

        # Query retro (< 2000)
        movies_retro = await get_movies_by_year_range(1900, 1999, limit=5, offset=0)
        self.assertEqual(len(movies_retro), 1)
        self.assertEqual(movies_retro[0]["title"], "Matrix")


if __name__ == "__main__":
    unittest.main()
