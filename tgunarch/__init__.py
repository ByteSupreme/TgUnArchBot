import logging
import time
from typing import Dict

# Third-party imports
from pyrogram import Client

# Local imports
from config import Config

# --- Constants ---
BOT_SESSION_NAME: str = "tgunarch-bot"
PLUGINS_ROOT: str = "plugins"
LOG_FILE_NAME: str = "tgunarch-bot.log"
LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(threadName)s - %(message)s"

# List of third-party loggers to set to WARNING level
THIRD_PARTY_LOGGERS_TO_QUIET: list[str] = [
    "asyncio",
    "aiohttp",
    "aiofiles",
    "dnspython",
    "GitPython",
    "motor",
    "Pillow",
    "psutil",
    "pyrogram",
    "requests",
]

# --- Logging Configuration ---

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE_NAME),
        logging.StreamHandler()
    ],
    format=LOG_FORMAT,
)

# Get the main logger for this application
LOGGER = logging.getLogger(__name__)
LOGGER.info("Basic logging configured.")

# Reduce verbosity from common third-party libraries
LOGGER.info(f"Setting log level to WARNING for: {', '.join(THIRD_PARTY_LOGGERS_TO_QUIET)}")
for logger_name in THIRD_PARTY_LOGGERS_TO_QUIET:
    logging.getLogger(logger_name).setLevel(logging.WARNING)


# --- Bot Initialization ---

boottime: float = time.time()
LOGGER.info(f"Application started at boot time: {boottime}")

# Define plugin structure
plugins: Dict[str, str] = dict(root=PLUGINS_ROOT)
LOGGER.info(f"Using plugins from root directory: '{PLUGINS_ROOT}'")

# Initialize the Pyrogram Client
unzipbot_client = Client(
    name=BOT_SESSION_NAME, # Session file name
    bot_token=Config.BOT_TOKEN,
    api_id=Config.APP_ID,
    api_hash=Config.API_HASH,
    plugins=plugins,
    sleep_threshold=7200,            # Same value as before
    max_concurrent_transmissions=3,  # Same value as before
)

LOGGER.info(f"Pyrogram client '{BOT_SESSION_NAME}' initialized.")

# --- Optional: Add a confirmation log message at the end ---
LOGGER.info("Initialization complete.")