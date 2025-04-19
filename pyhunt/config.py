import os
from dotenv import load_dotenv

load_dotenv()

ROOT_PATH = os.getenv("ROOT_PATH")

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

# Read max log count from environment variable, default to None (unlimited)
MAX_REPEAT = int(os.getenv("HUNT_MAX_REPEAT", 3))
