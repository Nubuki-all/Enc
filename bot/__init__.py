#    This file is part of the Compressor distribution.
#    Copyright (c) 2021 Danish_00
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/1Danish-00/CompressorQueue/blob/main/License> .


import asyncio
import glob
import inspect
import io
import itertools
import json
import logging
import math
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime as dt
from logging import DEBUG, INFO, basicConfig, getLogger, warning
from logging.handlers import RotatingFileHandler
from pathlib import Path

import aiohttp
import psutil
from html_telegraph_poster import TelegraphPoster
from pyrogram import Client
from telethon import Button, TelegramClient, errors, events, functions, types
from telethon.sessions import StringSession
from telethon.utils import pack_bot_file_id

from .config import *

botStartTime = time.time()

LOG_FILE_NAME = "Logs.txt"


if os.path.exists(LOG_FILE_NAME):
    with open(LOG_FILE_NAME, "r+") as f_d:
        f_d.truncate(0)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=2097152000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("FastTelethon").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
LOGS = logging.getLogger(__name__)

try:
    LOG_CHANNEL
except Exception:
    LOG_CHANNEL = ""

try:
    bot = TelegramClient(None, APP_ID, API_HASH)
    app = Client(
        "Encoder", api_id=APP_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=2
    )
except Exception as e:
    LOGS.info("Environment vars are missing! Kindly recheck.")
    LOGS.info("Bot is quiting...")
    LOGS.info(str(e))
    exit()


def enmoji():
    emoji = (
        "🤓",
        "😎",
        "🤠",
        "🌚",
        "🛰️",
        "❤️",
        "📡",
        "🥺",
        "🌝",
        "☺️",
        "😊",
        "😑",
        "🥸",
        "😵‍💫",
        "✅",
    )
    y = random.choice(emoji)
    return y


def enquip():
    quip = (
        "awake and ready to serve you, young master!",
        "Up!",
        "ready to encode from dusk till Dawn.",
        "ready and awaiting orders, Sir! Yes Sir!",
        "feeling lucky+",
        "(technically) a noble bot.",
        "the... Core of the Tsia Dungeon!",
        "stunned, yet not surprised, by your kind gesture.",
        "the eldest sister.",
        "the Archduke’s daughter, Maiodore in disguise.",
    )
    y = random.choice(quip)
    return y


async def startup():
    try:
        for i in OWNER.split():
            await bot.send_message(int(i), f"**I'm {enquip()} {enmoji()}**")
        if LOG_CHANNEL:
            me = await app.get_users("me")
            await bot.send_message(
                int(LOG_CHANNEL), f"**{me.first_name} is {enquip()} {enmoji()}**"
            )
    except BaseException:
        pass
