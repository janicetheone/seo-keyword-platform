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

# Seed keywords aligned to the 15 business template categories
SEED_KEYWORDS = [
    # 1. 宠物 / 动物
    "ai cat video", "ai dog video", "ai pet video", "animal olympics ai",
    "pet diving video", "talking pet ai", "dancing cat ai", "cute cat video generator",
    "ai animal video maker", "working pet video", "pet to human ai",

    # 2. 情感互动 / 人物关系
    "ai kiss video", "ai hug video", "ai french kiss generator",
    "fake celebrity date ai", "celebrity selfie ai", "ai couple video",
    "ai wedding video", "ai romance video maker", "ai valentine video",

    # 3. 运动 / 竞技
    "ai sports video", "ai workout video maker", "sports highlight ai",
    "ai basketball video", "ai soccer video", "ai game recap generator",
    "training montage ai", "home workout video ai",

    # 4. 影视 / 叙事 / 电影感
    "ai movie maker", "cinematic ai video", "ai short film generator",
    "ai movie trailer maker", "cinematic noir ai", "ai storytelling video",
    "ai drama video maker", "mystery video template ai",

    # 5. 音乐 / 舞蹈 / 演出
    "ai music video maker", "ai dance generator", "ai lip sync video",
    "tiktok dance ai", "ai music visualizer", "ai karaoke video",
    "ai lyric video maker", "ai choreography generator",

    # 6. 搞笑 / 猎奇 / 梗图整活
    "ai meme generator", "ai brainrot video", "ai funny video maker",
    "ai jiggle effect", "ai squish video", "npc trend ai video",
    "ai muscle meme", "ai glow up video", "ai viral video maker",

    # 7. 广告 / 电商 / 产品展示
    "ai ugc video", "ai product video", "ai commercial maker",
    "amazon product video ai", "ai 360 product video", "ai packshot generator",
    "ugc video ads ai", "ai brand video maker", "unboxing video ai",

    # 8. UGC / 虚拟人 / 口播
    "ai avatar video", "ai talking avatar", "ai digital human",
    "ai presenter generator", "consistent character ai video",
    "photo to talking video ai", "ai faceless video maker",
    "ai virtual influencer", "ai talking photo",

    # 9. 社媒平台模板
    "ai tiktok video maker", "ai instagram reel maker", "ai youtube shorts maker",
    "ai reels generator", "social media video ai", "ai vertical video maker",
    "youtube intro ai", "ai channel outro maker",

    # 10. 动漫 / 卡通 / 风格化
    "ghibli ai", "ai anime generator", "ai cartoon maker",
    "video to anime ai", "pixar ai filter", "ai simpsons filter",
    "ai art style video", "ai watercolor video", "photo to anime ai",

    # 11. 时尚 / 生活方式 / 写真
    "ai fashion video", "ai lookbook maker", "ai lifestyle video",
    "ai beauty video", "ai vlog maker", "ai ootd video",
    "luxury brand video ai", "ai editorial video",

    # 12. 美食 / ASMR
    "ai food video", "ai asmr video generator", "food porn video ai",
    "ai cooking video maker", "satisfying video ai", "ai mukbang video",
    "asmr cutting video ai", "glass fruits asmr ai",

    # 13. 新闻 / 教育 / 知识表达
    "ai news video maker", "ai explainer video", "ai tutorial video maker",
    "ai educational video", "ai whiteboard animation", "ai documentary maker",
    "ai infographic video", "ai podcast video maker",

    # 14. 旅行 / 城市 / 户外
    "ai travel video maker", "ai city vlog", "ai travel reel generator",
    "drone footage ai", "ai outdoor video", "ai landscape video",
    "ai road trip video", "cafe vlog ai maker",

    # 15. 节日 / 纪念 / 情绪
    "ai birthday video maker", "ai tribute video", "ai memorial video",
    "ai halloween filter", "ai christmas video", "ai cherry blossom video",
    "ai new year countdown video", "ai graduation video",

    # Competitor alternative queries
    "pollo ai alternative", "goenhan alternative", "invideo alternative",
    "viggle ai alternative", "kling ai alternative", "runway alternative free",
]
