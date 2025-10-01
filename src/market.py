import os
import random
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv

from database import read_market, write_market

load_dotenv(override=True)
