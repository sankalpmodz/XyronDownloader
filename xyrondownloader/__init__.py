import logging
import time

boot_time = time.time()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("pyrogram.parser.html").setLevel(logging.WARNING)