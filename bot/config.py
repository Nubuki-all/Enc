#    This file is part of the Encoder distribution.
#    Copyright (c) 2021 Danish_00, Nubuki-all
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
import traceback

from decouple import config

try:
    ALWAYS_DEPLOY_LATEST = config("ALWAYS_DEPLOY_LATEST", default=False, cast=bool)
    ALLOW_ACTION = config("ALLOW_ACTION", default=True, cast=bool)
    APP_ID = config("APP_ID", default=6, cast=int)
    API_HASH = config("API_HASH", default="eb06d4abfb49dc3eeb1aeb98ae0f581e")
    ARIA2_PORT = config("ARIA2_PORT", default=6800, cast=int)
    BOT_TOKEN = config("BOT_TOKEN")
    CACHE_DL = config("CACHE_DL", default=False, cast=bool)
    CAP_DECO = config("CAP_DECO", default="◉")
    C_LINK = config("C_LINK", default="@ANi_MiNE")
    CMD_SUFFIX = config("CMD_SUFFIX", default=str())
    DATABASE_URL = config("DATABASE_URL", default=None)
    DBNAME = config("DBNAME", default="ENC")
    DEV = config("DEV", default=123456, cast=int)
    DL_STUFF = config("DL_STUFF", default=None)
    DUMP_CHANNEL = config("DUMP_CHANNEL", default=0, cast=int)
    DUMP_LEECH = config("DUMP_LEECH", default=True, cast=bool)
    DYNO = config("DYNO", default=None)
    ENCODER = config("ENCODER", default=None)
    EXT_CAP = config("EXTENDED_CAPTIONS", default=True, cast=bool)
    WORKERS = config("WORKERS", default=2, cast=int)
    FBANNER = config("FBANNER", default=False, cast=bool)
    FCHANNEL = config("FCHANNEL", default=0, cast=int)
    FCHANNEL_STAT = config("FCHANNEL_STAT", default=0, cast=int)
    FCODEC = config("FCODEC", default=None)
    FFMPEG = config(
        "FFMPEG",
        default='ffmpeg -i "{}" -preset ultrafast -c:v libx265 -crf 27 -map 0:v -c:a aac -map 0:a -c:s copy -map 0:s? "{}"',
    )
    FL_CAP = config("FILENAME_AS_CAPTION", default=False, cast=bool)
    FS_THRESHOLD = config("FLOOD_SLEEP_THRESHOLD", default=600, cast=int)
    FSTICKER = config("FSTICKER", default=None)
    LOCK_ON_STARTUP = config("LOCK_ON_STARTUP", default=False, cast=bool)
    LOG_CHANNEL = config("LOG_CHANNEL", default=0, cast=int)
    LOGS_IN_CHANNEL = config("LOGS_IN_CHANNEL", default=False, cast=bool)
    MI_CAP = config("MI_IN_CAPTION", default=True, cast=bool)
    NO_BANNER = config("NO_BANNER", default=False, cast=bool)
    NO_TEMP_PM = config("NO_TEMP_PM", default=False, cast=bool)
    OVR = config("OVR", default=None)
    OWNER = config("OWNER")
    PAUSE_ON_DL_INFO = config("PODI", default=True, cast=bool)
    QBIT_PORT = config("QBIT_PORT", default=8090, cast=int)
    QBIT_TIMEOUT = config("QBIT_TIMEOUT", default=20, cast=int)
    RSS_CHAT = config("RSS_CHAT", default=-1001339167595, cast=int)
    RSS_DELAY = config("RSS_DELAY", default=60, cast=int)
    RELEASER = config("RELEASER", default="A-M|ANi-MiNE")
    TELEGRAPH_API = config("TELEGRAPH_API", default="https://api.telegra.ph")
    TELEGRAPH_AUTHOR = config("TELEGRAPH_AUTHOR", default=None)
    TEMP_USER = config("TEMP_USERS", default=str())
    TG_DL_CLIENT = config("TG_DL_CLIENT", default="pyrogram")
    TG_UL_CLIENT = config("TG_UL_CLIENT", default="pyrogram")
    THUMB = config("THUMBNAIL", default=None)
except Exception:
    print("Environment vars Missing; or")
    print("something went wrong")
    print(traceback.format_exc())
    exit()
