"""
Automated Movie Population Script for Kinochi Bot Pro.
Populates all 12 genres with popular movies, descriptions, ratings, and valid Telegram file_ids.
"""
import asyncio
import logging
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile

from config import settings
from database import init_db, add_movie, get_movie_by_code, get_movies_by_genre

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("populate_movies")

GENRES_LIST = [
    "Jangari", "Komediya", "Fantastika", "Qo'rqinchli",
    "Drama", "Melodrama", "Multfilm", "Kriminal",
    "Tarixiy", "Detektiv", "Anime", "Sarguzasht"
]

# Local video clips to upload for obtaining real Telegram file_ids
LOCAL_VIDEOS = {
    "action": "/home/mr-x/anime_test_production/production/motion_clips/SHOT_001_motion.mp4",
    "drama": "/home/mr-x/anime_test_production/production/motion_clips/SHOT_002_motion.mp4",
    "anime": "/home/mr-x/mangabo_anime_production/final_render/master_episode_mangabo_1080p.mp4",
    "default": "BAACAgIAAxkDAAMwavyw2auNeeU7hNNIDN6TD1CELDkAAsu0AALZXehL0p-mIFLld6Q9BA"
}


async def obtain_file_ids(bot: Bot) -> dict[str, str]:
    """Upload sample videos to admin to get valid, working Telegram file_ids."""
    file_ids = {"default": LOCAL_VIDEOS["default"]}
    admin_id = settings.ADMIN_IDS[0]
    
    for key in ["action", "drama", "anime"]:
        filepath = Path(LOCAL_VIDEOS[key])
        if filepath.exists():
            try:
                logger.info(f"Uploading {key} sample ({filepath.name})...")
                msg = await bot.send_video(
                    chat_id=admin_id,
                    video=FSInputFile(str(filepath)),
                    caption=f"🎬 <b>{key.upper()}</b> namunaviy video yuklandi (File ID saqlanmoqda)."
                )
                file_ids[key] = msg.video.file_id
                logger.info(f"Obtained file_id for {key}: {file_ids[key][:25]}...")
            except Exception as e:
                logger.warning(f"Could not upload {key} clip: {e}. Using fallback default.")
                file_ids[key] = file_ids["default"]
        else:
            file_ids[key] = file_ids["default"]
            
    return file_ids


MOVIES_CATALOG = [
    {
        "code": "101",
        "title": "Jon Uik 4",
        "original_title": "John Wick: Chapter 4",
        "year": 2023,
        "country": "AQSH, Germaniya",
        "genres": "Jangari, Kriminal, Triller",
        "category": "Jangari",
        "language": "O'zbek tilida",
        "duration": "2 soat 49 daqiqa",
        "rating": 8.2,
        "video_type": "action",
        "description": "Jon Uik Oliy Stol ustidan g'alaba qozonish yo'lini topadi. Ammo erkinlikka erishishdan oldin, u butun dunyo bo'ylab kuchli ittifoqlarga ega bo'lgan yangi dushmanga qarshi kurashishi kerak."
    },
    {
        "code": "102",
        "title": "Uyda Yolg'iz",
        "original_title": "Home Alone",
        "year": 1990,
        "country": "AQSH",
        "genres": "Komediya, Oila",
        "category": "Komediya",
        "language": "O'zbek tilida",
        "duration": "1 soat 43 daqiqa",
        "rating": 7.7,
        "video_type": "drama",
        "description": "Katta oila Rojdestvo ta'tiliga ketayotganda tasodifan 8 yoshli Kevinni uyda unutib qoldiradi. Kevin mustaqil yashashni o'rganadi va ikki o'g'ridan uyini mardonavor himoya qiladi."
    },
    {
        "code": "103",
        "title": "Avatar: Suv Yo'li",
        "original_title": "Avatar: The Way of Water",
        "year": 2022,
        "country": "AQSH",
        "genres": "Fantastika, Sarguzasht, Jangari",
        "category": "Fantastika",
        "language": "O'zbek tilida",
        "duration": "3 soat 12 daqiqa",
        "rating": 7.8,
        "video_type": "action",
        "description": "Jeyk Salli va Neytiri oila qurib, Pandora sayyorasida tinch hayot kechirishga intilishadi. Biroq qadimgi xavf yana qaytib kelgach, ular o'z xalqini va okean qabilasini asrash uchun jangga kirishadi."
    },
    {
        "code": "104",
        "title": "Astral: Qizil Eshik",
        "original_title": "Insidious: The Red Door",
        "year": 2023,
        "country": "AQSH, Kanada",
        "genres": "Qo'rqinchli, Detektiv",
        "category": "Qo'rqinchli",
        "language": "O'zbek tilida",
        "duration": "1 soat 47 daqiqa",
        "rating": 6.8,
        "video_type": "drama",
        "description": "Lambertlar oilasi o'zlarining qora o'tmishidagi dahshatli iblislarni butunlay daf qilish uchun Qizil Eshik ortidagi zulmat olamiga yana bir bor kirishga majbur bo'ladi."
    },
    {
        "code": "105",
        "title": "Oppengeymer",
        "original_title": "Oppenheimer",
        "year": 2023,
        "country": "AQSH, Buyuk Britaniya",
        "genres": "Drama, Tarixiy, Biografiya",
        "category": "Drama",
        "language": "O'zbek tilida",
        "duration": "3 soat 00 daqiqa",
        "rating": 8.9,
        "video_type": "drama",
        "description": "Dunyo tarixini butunlay o'zgartirgan atom bombasining yaratuvchisi Robert Oppengeymer va uning Manhattan loyihasidagi fojiali, murakkab hayoti haqida xronikal drama."
    },
    {
        "code": "106",
        "title": "Titanik",
        "original_title": "Titanic",
        "year": 1997,
        "country": "AQSH",
        "genres": "Melodrama, Drama, Tarixiy",
        "category": "Melodrama",
        "language": "O'zbek tilida",
        "duration": "3 soat 14 daqiqa",
        "rating": 7.9,
        "video_type": "drama",
        "description": "Hashamatli afsonaviy kemaning birinchi va so'nggi sayohatida turli tabaqadan bo'lgan yosh yigit Jek va aslzoda qiz Rouz o'rtasidagi abadiy, unutilmas muhabbat qissasi."
    },
    {
        "code": "107",
        "title": "Kung Fu Panda 4",
        "original_title": "Kung Fu Panda 4",
        "year": 2024,
        "country": "AQSH, Xitoy",
        "genres": "Multfilm, Komediya, Sarguzasht",
        "category": "Multfilm",
        "language": "O'zbek tilida",
        "duration": "1 soat 34 daqiqa",
        "rating": 7.1,
        "video_type": "action",
        "description": "Ajdaho Jangchisi Po endi Tinchlik Vodiysining Ruhiy Rahbari bo'lishi kerak. Ammo yangi yovuz sehrgar Xameleon barcha sobiq ustalar mahoratini o'g'irlashga urinadi."
    },
    {
        "code": "108",
        "title": "Cho'qintirgan Ota",
        "original_title": "The Godfather",
        "year": 1972,
        "country": "AQSH",
        "genres": "Kriminal, Drama",
        "category": "Kriminal",
        "language": "O'zbek tilida",
        "duration": "2 soat 55 daqiqa",
        "rating": 9.2,
        "video_type": "drama",
        "description": "Nyu-Yorkdagi qudratli sitsiliyalik mafiya klanining rahbari Don Vito Korleone va uning kenja o'g'li Mayklning oilaviy imperiya taxtiga o'tirish yo'li haqida jahon kinosi durdonasi."
    },
    {
        "code": "109",
        "title": "Gladiator 2",
        "original_title": "Gladiator II",
        "year": 2024,
        "country": "AQSH, Buyuk Britaniya",
        "genres": "Tarixiy, Jangari, Drama",
        "category": "Tarixiy",
        "language": "O'zbek tilida",
        "duration": "2 soat 28 daqiqa",
        "rating": 7.5,
        "video_type": "action",
        "description": "Maksimusning o'limidan yillar o'tib, Lyutsiy Rimning zolim imperatorlariga qarshi Kolizey arenasida jang qiladi va Rim xalqiga erkinlik keltirish uchun kurashadi."
    },
    {
        "code": "110",
        "title": "Sherlok Xolms",
        "original_title": "Sherlock Holmes",
        "year": 2009,
        "country": "AQSH, Buyuk Britaniya",
        "genres": "Detektiv, Sarguzasht, Jangari",
        "category": "Detektiv",
        "language": "O'zbek tilida",
        "duration": "2 soat 08 daqiqa",
        "rating": 7.6,
        "video_type": "drama",
        "description": "Afsonaviy detektiv Sherlok Xolms va uning sadoqatli hamrohi doktor Vatson Londondagi mistik qotilliklarni ochish va butun Angliyani xavfdan asrash uchun aql va musht mahoratini ishga soladi."
    },
    {
        "code": "111",
        "title": "Mangabox Premyera",
        "original_title": "Mangabox Ultimate Anime",
        "year": 2024,
        "country": "Yaponiya, O'zbekiston",
        "genres": "Anime, Jangari, Fantastika",
        "category": "Anime",
        "language": "O'zbek tilida",
        "duration": "45 daqiqa",
        "rating": 8.5,
        "video_type": "anime",
        "description": "Mangabox.uz afsonaviy mangasi asosida maxsus yaratilgan to'liq metrajli anime qismi. Dinamik Sakuga jang sahnalari va unutilmas qahramonlar to'qnashuvi."
    },
    {
        "code": "112",
        "title": "Karib Dengizi Qaroqchilari",
        "original_title": "Pirates of the Caribbean: The Curse of the Black Pearl",
        "year": 2003,
        "country": "AQSH",
        "genres": "Sarguzasht, Fantastika, Jangari",
        "category": "Sarguzasht",
        "language": "O'zbek tilida",
        "duration": "2 soat 23 daqiqa",
        "rating": 8.1,
        "video_type": "action",
        "description": "Kapitan Jek Chittak va yosh temirchi Uill Terner la'natlangan qaroqchilar qo'liga tushgan gubernator qizi Elizabet Suonni qutqarish uchun xavfli sarguzashtga otlanadilar."
    }
]


async def populate():
    """Populate movies for all categories."""
    await init_db()
    bot = Bot(token=settings.BOT_TOKEN)
    
    logger.info("1. Obtaining working Telegram file_ids...")
    file_ids = await obtain_file_ids(bot)
    
    logger.info("2. Inserting movies into database...")
    added_count = 0
    updated_count = 0
    
    for item in MOVIES_CATALOG:
        existing = await get_movie_by_code(item["code"])
        target_file_id = file_ids.get(item["video_type"], file_ids["default"])
        
        movie_dict = {
            "code": item["code"],
            "title": item["title"],
            "original_title": item["original_title"],
            "year": item["year"],
            "country": item["country"],
            "genres": item["genres"],
            "language": item["language"],
            "duration": item["duration"],
            "rating": item["rating"],
            "description": item["description"],
            "quality_720_file_id": target_file_id,
            "quality_1080_file_id": target_file_id,
            "views_count": 100,
            "downloads_count": 50,
            "likes_count": 25,
            "is_vip_only": 0,
            "is_series": 0,
            "is_active": 1
        }
        
        if not existing:
            await add_movie(movie_dict)
            logger.info(f"Added movie [{item['code']}] {item['title']} ({item['category']})")
            added_count += 1
        else:
            logger.info(f"Movie [{item['code']}] already exists, skipping.")
            updated_count += 1
            
    logger.info(f"Done! Added: {added_count}, Existing: {updated_count}")
    
    # 3. Verification Gate: Check every single genre
    logger.info("3. Verifying all 12 categories...")
    verification_errors = []
    for g in GENRES_LIST:
        movies = await get_movies_by_genre(g, limit=5)
        if movies:
            logger.info(f"✅ Janr '{g}': Topildi {len(movies)} ta kino ({', '.join([m['title'] for m in movies])})")
        else:
            logger.error(f"❌ Janr '{g}': Kino topilmadi!")
            verification_errors.append(g)
            
    await bot.session.close()
    
    if verification_errors:
        raise RuntimeError(f"Verification failed for genres: {verification_errors}")
    else:
        logger.info("🎉 SUCCESS! All 12 categories have been verified and populated.")


if __name__ == "__main__":
    asyncio.run(populate())
