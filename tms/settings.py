import sys
from pathlib import Path

from loguru import logger

PROJECTNAME = "tms-bot"

BASEDIR = Path(__file__).resolve().parent.parent
CONFIGPATH = BASEDIR / "config.yaml"
OUTPUTDIR = BASEDIR / "output"


# Loguru config
logger.remove()
logger.add(
    BASEDIR / f"{PROJECTNAME}.log",
    enqueue=True,
    backtrace=True,
)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


# URLS
TMS_BASE = "https://tms17.nepsetms.com.np"
HEADLESS = False
DRIVERNAME = "geckodriver.exe"
