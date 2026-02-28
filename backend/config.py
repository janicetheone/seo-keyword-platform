from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'seo_keywords.db'}"
    secret_key: str = "dev-secret-key"
    debug: bool = True

    # Rate limiting
    autocomplete_requests_per_minute: int = 30
    trends_requests_per_minute: int = 10
    serp_requests_per_minute: int = 10
    competitor_requests_per_minute: int = 5

    # Expansion
    max_expansion_depth: int = 2
    top_n_for_recursive: int = 5

    model_config = {"env_file": str(BASE_DIR / ".env")}


settings = Settings()

# Seed keywords — specific template names from competitor analysis
# (Pollo AI, GoEnhance, InVideo) across 16 business categories
SEED_KEYWORDS = [
    # 1. 宠物 / 动物 — Pet & Animal
    "pet kissing video", "pet hug video", "ai selfie with pets",
    "animal olympics ai", "dog diving challenge ai", "pet to human ai",
    "working pet video", "bear chase ai", "animal pov adventure",
    "pet celebrity video", "talking pet ai", "dancing cat ai",

    # 2. 情感互动 / 人物关系 — Romance & Social
    "ai kissing video", "ai french kiss video", "blowing kisses ai",
    "ai hug generator", "reunion hug video", "ai fake date video",
    "romantic night out ai", "polaroid duo selfie", "couple memory clip ai",
    "celebrity selfie ai", "fan meet ai video",

    # 3. 搞笑 / 整活 / 猎奇 — Meme & Viral
    "ai twerk generator", "ai jiggle video effect", "into the mouth ai",
    "squish it ai", "drip flip ai", "drunk vision video ai",
    "ufo effect ai", "kaleido video ai", "face swap meme generator",
    "funny reaction meme ai", "npc trend ai video", "ai brainrot video",

    # 4. 动漫 / 卡通 / 风格化 — Anime & Style
    "ghibli ai generator", "video to anime ai", "ai animation generator",
    "pixar ai generator", "ai cartoon generator", "video into cartoon ai",
    "character animation ai", "live 2d animation ai", "ai simpsons character generator",
    "snoopy filter ai", "anime filter ai",

    # 5. 人物形象 / 虚拟人 / 口播 — UGC Avatar
    "photo to video avatar ai", "ai talking avatar", "consistent character video ai",
    "video face swap", "multiple face swap ai", "ai baby filter",
    "ai bald filter", "ai beardless filter", "pregnant ai filter",
    "ai age filter", "face aging ai", "ai talking photo",

    # 6. 运动 / 舞蹈 / 演出 — Dance & Sports
    "ai dance generator", "dancing girl ai", "5 minute home workout ai",
    "home workout video ai", "performance clip ai", "stage motion video ai",
    "instrument playing ai", "playing guitar ai video", "sports highlight ai",
    "training montage ai",

    # 7. 音乐 / MV — Music Video
    "music video ai maker", "jazz club invite video", "nature meditation video ai",
    "moana nursery rhyme ai", "kids song video ai", "performance music cut ai",
    "ai lip sync video", "lyric video ai", "ai karaoke video",
    "music visualizer ai",

    # 8. 影视 / 叙事 / 电影感 — Cinematic Story
    "cinematic noir ai", "hero walk video ai", "mystery storytelling ai",
    "first person pov video ai", "movie scene generator ai", "faceless story video ai",
    "short film ai generator", "ai movie trailer maker", "director cut ai",
    "horror video ai",

    # 9. 社交媒体 / 平台模板 — Social Platform
    "instagram video maker ai", "tiktok video maker ai", "youtube shorts maker ai",
    "instagram reels ai", "linkedin video maker ai", "facebook video maker ai",
    "youtube intro maker ai", "youtube outro maker ai", "daily vlog maker ai",
    "celebrity video ai",

    # 10. 广告 / 电商 / 产品展示 — Ads & Ecommerce
    "ugc video ads ai", "beard oil ugc ad", "brand promo video ai",
    "mercedes promo video ai", "360 product video ai", "hero shot video ai",
    "packshot 360 ai", "amazon a plus content ai", "amazon primary image ai",
    "catalogue photography ai", "product demo video ai",

    # 11. 时尚 / 生活方式 — Fashion & Lifestyle
    "fashion lifestyle video ai", "high end luxury video ai",
    "daily vlog ai", "day in my life ai video", "lookbook video ai",
    "best work from cafe video", "cafe vlog ai", "indoor studio video ai",
    "retro modern video ai", "ootd video ai",

    # 12. 美食 / ASMR — Food & ASMR
    "food porn video ai", "glass fruits cutting asmr", "ai asmr video generator",
    "culinary art promo video", "restaurant promo video ai",
    "satisfying cutting video ai", "mukbang video ai", "cooking video ai",

    # 13. 旅行 / 户外 / 城市 — Travel & Outdoor
    "iconic locations video ai", "the great outdoors video ai",
    "b roll video ai", "travel photo motion ai", "nature photo animation ai",
    "drone footage ai", "city vlog ai", "road trip video ai",
    "landscape video ai",

    # 14. 资讯 / 教育 / 知识 — News & Education
    "news video ai maker", "education explainer video ai",
    "the reviewer video ai", "faceless video maker ai", "faceless channel ai",
    "product review video ai", "ai tutorial video maker", "ai documentary maker",
    "whiteboard animation ai",

    # 15. 节日 / 纪念 / 情绪 — Holiday & Celebration
    "birthday video ai maker", "tribute video ai", "memorial video ai",
    "old photo animation ai", "photo restoration ai", "holiday memory reel ai",
    "halloween effect ai", "christmas video ai", "cherry blossom video ai",
    "graduation video ai",

    # 16. 创意特效 / 后期工具 — Creative Effects
    "video effect ai generator", "ai video filter", "vhs effect ai",
    "whip pan video ai", "camera angles ai", "extract shot ai",
    "ai relight video", "ai colorist tool", "inpaint and cleanup video ai",
    "video cleanup ai", "prop swap video ai", "re frame video ai",
    "virtual production ai", "slow motion ai", "speed ramp ai",

    # Competitor intent / alternative queries
    "pollo ai alternative", "goenhan alternative", "invideo alternative",
    "viggle ai alternative", "kling ai alternative", "runway ml alternative",
]
