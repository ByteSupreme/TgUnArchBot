import os

import psutil


class Config:
    APP_ID = xxxxx
    API_HASH = "xxxxx"
    BASE_LANGUAGE = "en"
    AUTH_CHANNEL = -100xxxx
    CHANNEL_URL = "xxxx"
    #1800 seconds = 30 minutes
    FREE_USER_TIMER = 1800
    BOT_TOKEN = "xxxxx"
    BOT_THUMB = f"{os.path.dirname(__file__)}/bot_thumb.jpg"
    BOT_USERNAME = "xxxxxxx"
    BOT_OWNER = xxxxxx
    OWNER_USERNAME = "xxxxx"
    # Default chunk size (0.005 MB → 1024*6) Increase if you need faster downloads
    CHUNK_SIZE = 1024 * 1024 * 10  # 10 MB
    DOWNLOAD_LOCATION = f"{os.path.dirname(__file__)}/Downloaded"
    IS_HEROKU = "".startswith("worker.")
    LOCKFILE = "tgunarch.lock"
    LOGS_CHANNEL = -100xxxx
    MAX_CONCURRENT_TASKS = 75
    MAX_MESSAGE_LENGTH = 4096
    MAX_CPU_CORES_COUNT = psutil.cpu_count(logical=False)
    MAX_CPU_USAGE = 80
    # 512 MB by default for Heroku, unlimited otherwise
    MAX_RAM_AMOUNT_KB = 1024 * 512 if IS_HEROKU else -1
    MAX_RAM_USAGE = 80
    MAX_TASK_DURATION_EXTRACT = 120 * 60  # 2 hours (in seconds)
    MAX_TASK_DURATION_MERGE = 240 * 60  # 4 hours (in seconds)
    # Files under that size will not display a progress bar while uploading
    MIN_SIZE_PROGRESS = 1024 * 1024 * 50  # 50 MB
    MONGODB_URL = "xxxxx"
    MONGODB_DBNAME = "TgUnArchBot"
    TG_MAX_SIZE = 2097152000
    THUMB_LOCATION = f"{os.path.dirname(__file__)}/Thumbnails"
    VERSION = "1.0"
