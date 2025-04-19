import os
from dotenv import load_dotenv

load_dotenv()


# Log level mapping similar to Python's logging module
LOG_LEVELS = {
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
    "critical": 50,
}
# Read log level from environment variable, default to INFO
_log_level_name = os.getenv("HUNT_LEVEL", "INFO").lower()
LOG_LEVEL = LOG_LEVELS.get(_log_level_name, 20)  # default INFO if invalid

ROOT_DIR = os.getenv("ROOT_DIR")

# Read max log count from environment variable, default to None (unlimited)
MAX_REPEAT = int(os.getenv("HUNT_MAX_REPEAT", 3))

# Read elapsed time display setting from environment variable, default to True
ELAPSED = os.getenv("ELAPSED", "True").lower() in ("true", "1", "yes")
