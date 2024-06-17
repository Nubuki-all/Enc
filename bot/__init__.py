#    This file is part of the Encoder distribution.
#    Copyright (c) 2023 Danish_00, Nubuki-all
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
# https://github.com/Nubuki-all/Enc/blob/main/License> .


import argparse
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
import shlex
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime as dt
from logging import DEBUG, INFO, basicConfig, getLogger, warning
from logging.handlers import RotatingFileHandler
from pathlib import Path

import aiohttp
import aria2p
from html_telegraph_poster import TelegraphPoster
from html_telegraph_poster import errors as telegraph_errors
from pyrogram import Client
from pyrogram import errors as pyro_errors
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from qbittorrentapi import Client as qbClient
from telethon import Button, TelegramClient, errors, events, functions, types
from telethon.sessions import StringSession
from telethon.utils import pack_bot_file_id

from .config import _bot, conf

batch_lock = asyncio.Lock()
bot_id = conf.BOT_TOKEN.split(":", 1)[0]
botStartTime = time.time()
caption_file = "NO_CAPTION"
ffmpeg_file = "ffmpeg.txt"
mux_file = "mux.txt"
filter_file = "filter.txt"
home_dir = os.getcwd()
local_qdb = ".local_queue.pkl"
local_qdb2 = ".local_bqueue.pkl"
local_rdb = ".local_rssdb.pkl"
local_udb = ".t_users.pkl"
log_file_name = "Logs.txt"
parse_file = "NO_PARSE"
queue_lock = asyncio.Lock()
rename_file = "Auto-rename.txt"
rss_dict_lock = asyncio.Lock()
thumb = "thumb.jpg"
version_file = "version.txt"

_bot.repo_branch = (
    subprocess.check_output(["git rev-parse --abbrev-ref HEAD"], shell=True)
    .decode()
    .strip()
    if os.path.exists(".git")
    else None
)

tgp_author = tgp_author_url = None
if conf.TELEGRAPH_AUTHOR and conf.TELEGRAPH_AUTHOR.split("|")[0].casefold() != "auto":
    tgp_author = conf.TELEGRAPH_AUTHOR.split("|")[0]

if conf.TELEGRAPH_AUTHOR and len(conf.TELEGRAPH_AUTHOR.split("|")) > 1:
    if (tgp_author_url := conf.TELEGRAPH_AUTHOR.split("|")[1]).casefold() == "auto":
        tgp_author_url = None


if "|" in conf.RELEASER:
    release_name = conf.RELEASER.split("|")[0]
    release_name_b = conf.RELEASER.split("|")[1]
else:
    release_name = conf.RELEASER
    release_name_b = conf.RELEASER

release_name = f"[{release_name.strip()}]"
release_name_b = f"[{release_name_b.strip()}]"


if os.path.exists(log_file_name):
    with open(log_file_name, "r+") as f_d:
        f_d.truncate(0)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(log_file_name, maxBytes=2097152000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
logging.getLogger("FastTelethon").setLevel(logging.INFO)
# logging.getLogger("telethon.messagebox").setLevel(logging.NOTSET + 1)
no_verbose = [
    "telethon.client.updates",
    "telethon.client.users",
    "pyrogram.session.session",
    "pyrogram.connection.connection",
]
if _bot.repo_branch == "stable":
    for item in no_verbose:
        logging.getLogger(item).setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.INFO)
LOGS = logging.getLogger(__name__)


# pause_types
cd_pause = "cd_pause"
dl_pause = "dl_pause"
id_pause = "id_pause"


if sys.version_info < (3, 10):
    LOGS.critical("Please use Python 3.10+")
    exit(1)


tgp_client = TelegraphPoster(use_api=True, telegraph_api_url=conf.TELEGRAPH_API)


try:
    tele = TelegramClient(
        "tele",
        conf.APP_ID,
        conf.API_HASH,
        catch_up=True,
        flood_sleep_threshold=conf.FS_THRESHOLD,
    )
    pyro = Client(
        "pyro",
        api_id=conf.APP_ID,
        api_hash=conf.API_HASH,
        bot_token=conf.BOT_TOKEN,
        sleep_threshold=conf.FS_THRESHOLD,
        workers=conf.WORKERS,
    )
except Exception as e:
    LOGS.info("Environment vars are missing! Kindly recheck.")
    LOGS.info("Bot is quiting...")
    LOGS.info(str(e))
    exit(1)
