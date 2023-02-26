#    This file is part of the CompressorQueue distribution.
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
import io
import json
import math
import os
import subprocess
import time
from io import StringIO
from re import match as re_match
from subprocess import run as bashrun

from pymongo import MongoClient
from quote import quote
from random_word import RandomWords

from . import *
from .config import *

UNLOCK_UNSTABLE = []
DOWNLOAD_CANCEL = []
USER_MAN = []
GROUPENC = []
LOCKFILE = []
VERSION2 = []
STARTUP = []
WORKING = []
EVENT2 = []
QUEUE = {}
OK = {}

FINISHED_PROGRESS_STR = "🧡"
UN_FINISHED_PROGRESS_STR = "🤍"
MAX_MESSAGE_LENGTH = 4096
URL_REGEX = r"^(https?://|ftp://)?(www\.)?[^/\s]+\.[^/\s:]+(:\d+)?(/[^?\s]*)?(\?[^#\s]*)?(#.*)?$"

uptime = dt.now()

if EABF is True:
    UNLOCK_UNSTABLE.append(1)

if THUMB:
    os.system(f"wget {THUMB} -O thumb.jpg")

if ICON:
    os.system(f"wget {ICON} -O icon.png")

ffmpegfile = Path("ffmpeg.txt")
if ffmpegfile.is_file():
    pass
else:
    file = open(ffmpegfile, "w")
    file.write(str(FFMPEG) + "\n")
    file.close()

if not os.path.isdir("downloads/"):
    os.mkdir("downloads/")
if not os.path.isdir("encode/"):
    os.mkdir("encode/")
if not os.path.isdir("temp/"):
    os.mkdir("temp/")
if not os.path.isdir("thumb/"):
    os.mkdir("thumb/")

if DATABASE_URL:
    cluster = MongoClient(DATABASE_URL)
    db = cluster[DBNAME]
    queue = db["queue"]
    ffmpegdb = db["code"]
    filterz = db["filter"]
    queries = queue.find({})
    for query in queries:
        que = str(query["queue"])
        io = StringIO(que)
        pre = json.load(io)
        QUEUE.update(pre)
    queries = ffmpegdb.find({})
    for query in queries:
        que = query["queue"]
        que = que[0]
        io = StringIO(que)
        pre = json.load(io)
        if len(pre) < 5:
            pass
        else:
            file = open("ffmpeg.txt", "w")
            file.write(str(pre) + "\n")
            file.close()
    queries = filterz.find({})
    for query in queries:
        que = query["queue"]
        que = que[0]
        io = StringIO(que)
        pre = json.load(io)
        if len(pre) < 5:
            pass
        else:
            file = open("filter.txt", "w")
            file.write(str(pre) + "\n")
            file.close()
else:
    ffmpegdb = ""
    filterz = ""


video_mimetype = [
    "video/x-flv",
    "video/mp4",
    "application/x-mpegURL",
    "video/MP2T",
    "video/3gpp",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/x-matroska",
    "video/webm",
    "video/x-m4v",
    "video/quicktime",
    "video/mpeg",
]


def stdr(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if len(str(minutes)) == 1:
        minutes = "0" + str(minutes)
    if len(str(hours)) == 1:
        hours = "0" + str(hours)
    if len(str(seconds)) == 1:
        seconds = "0" + str(seconds)
    dur = (
        ((str(hours) + ":") if hours else "00:")
        + ((str(minutes) + ":") if minutes else "00:")
        + ((str(seconds)) if seconds else "")
    )
    return dur


def time_formatter(seconds: float) -> str:
    """humanize time"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
    )
    return tmp[:-2]


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
    )
    return tmp[:-2]


def ts(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
        + ((str(milliseconds) + "ms, ") if milliseconds else "")
    )
    return tmp[:-2]


def is_url(url):
    url = re_match(URL_REGEX, url)
    return bool(url)


def is_video_file(filename):
    video_file_extensions = (
        ".3g2",
        ".3gp",
        ".3gp2",
        ".3gpp",
        ".avc",
        ".avd",
        ".avi",
        ".evo",
        ".fli",
        ".flv",
        ".flx",
        ".m4u",
        ".m4v",
        ".mkv",
        ".mov",
        ".movie",
        ".mp21",
        ".mp21",
        ".mp2v",
        ".mp4",
        ".mp4v",
        ".mpeg",
        ".mpeg1",
        ".mpeg4",
        ".mpf",
        ".mpg",
        ".mpg2",
        ".xvid",
    )
    if filename.endswith((video_file_extensions)):
        return True


def hbs(size):
    if not size:
        return ""
    power = 2**10
    raised_to_pow = 0
    dict_power_n = {0: "B", 1: "K", 2: "M", 3: "G", 4: "T", 5: "P"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


No_Flood = {}


async def updater():
    try:
        await qclean()
        await varssaver("0", "update")
        bashrun(["python3", "update.py"])
        os.execl(sys.executable, sys.executable, "-m", "bot")
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def varsgetter(files):
    evars = ""
    if files.is_file():
        with open(files, "r") as file:
            evars = file.read().rstrip()
            file.close()
    return evars


async def varssaver(evars, files):
    if evars:
        file = open(files, "w")
        file.write(str(evars) + "\n")
        file.close()


async def channel_log(error):
    if LOG_CHANNEL and UNLOCK_UNSTABLE:
        try:
            log = int(LOG_CHANNEL)
            await bot.send_message(
                log,
                f"**#ERROR\n\n⛱️ Summary of what happened:**\n`{error}`\n\nTo restict error messages to logs set the EABF vars to False. {enmoji()}",
            )
        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)


async def get_leech_file():
    try:
        dt_ = glob.glob("downloads/*")
        data = max(dt_, key=os.path.getctime)
        dat = data.replace("downloads/", "")
    except Exception:
        dat = ""
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
    return dat


async def get_leech_name(url):
    try:
        os.system(f"aria2c --follow-torrent=false -d temp {url}")
        dt_ = glob.glob("temp/*")
        data = max(dt_, key=os.path.getctime)
        dat = data.replace("temp/", "")
        filename = dat.split(".torrent", maxsplit=1)[-2]
        if is_video_file(filename) is True:
            pass
        else:
            filename = ""
        os.system("rm -rf temp/*")
    except Exception:
        filename = None
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)
    return filename


async def enquoter(msg, rply):
    try:
        quotes = await enquotes()
        await rply.edit(f"**{msg}**\n\n~while you wait~\n\n{quotes}")
        await asyncio.sleep(5)
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def enquotes():
    res = ""
    while not res:
        try:
            r = RandomWords()
            w = r.get_random_word()
            res = quote(w, limit=1)
            for i in range(len(res)):
                result = res[i]["quote"]
                result2 = res[i]["author"]
                y = enmoji()
                output = (result[:2045] + "…") if len(result) > 2046 else result
                output = f"{y} **{result2}:** `{output}`"
        except Exception:
            pass
    return output


async def progress_for_pyrogram(current, total, bot, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        status = "downloads" + "/status.json"
        if os.path.exists(status):
            with open(status, "r+") as f:
                statusMsg = json.load(f)
                if not statusMsg["running"]:
                    bot.stop_transmission()
        speed = current / diff
        time_to_completion = time_formatter(int((total - current) / speed))

        progress = "{0}{1} \n<b>Progress:</b> `{2}%`\n".format(
            "".join(
                [FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]
            ),
            "".join(
                [
                    UN_FINISHED_PROGRESS_STR
                    for i in range(10 - math.floor(percentage / 10))
                ]
            ),
            round(percentage, 2),
        )

        tmp = progress + "`{0} of {1}`\n**Speed:** `{2}/s`\n**ETA:** `{3}`\n".format(
            hbs(current),
            hbs(total),
            hbs(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            time_to_completion if time_to_completion else "0 s",
        )
        try:
            if not message.photo:
                await message.edit_text(text="{}\n {}".format(ud_type, tmp))
            else:
                await message.edit_caption(caption="{}\n {}".format(ud_type, tmp))
        except BaseException:
            pass


async def progress(current, total, event, start, type_of_ps, file=None):
    now = time.time()
    if No_Flood.get(event.chat_id):
        if No_Flood[event.chat_id].get(event.id):
            if (now - No_Flood[event.chat_id][event.id]) < 1.1:
                return
        else:
            No_Flood[event.chat_id].update({event.id: now})
    else:
        No_Flood.update({event.chat_id: {event.id: now}})
    diff = time.time() - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        time_to_completion = round((total - current) / speed) * 1000
        progress_str = "**Progress**: `{0}{1} {2}%` \n".format(
            "".join(["🧡" for i in range(math.floor(percentage / 10))]),
            "".join(["🤍" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 4),
        )
        tmp = (
            progress_str
            + "**Completed**: `{0} of {1}`\n**Speed**: `{2}/s` \n**ETA**: `{3}` \n".format(
                hbs(current),
                hbs(total),
                hbs(speed),
                ts(time_to_completion),
            )
        )
        if file:
            await event.edit(
                "`✦ {}`\n\n`File Name: {}`\n\n{}".format(type_of_ps, file, tmp)
            )
        else:
            await event.edit("`✦ {}`\n\n{}".format(type_of_ps, tmp))


async def info(file, event):
    process = subprocess.Popen(
        ["mediainfo", file, "--Output=HTML"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = process.communicate()
    out = stdout.decode()
    client = TelegraphPoster(use_api=True)
    client.create_api_token("Mediainfo")
    page = client.post(
        title="Mediainfo",
        author="ANi_MiRROR",
        author_url="https://t.me/Ani_Mirror",
        # author=((await event.client.get_me()).first_name),
        # author_url=f"https://t.me/{((await
        # event.client.get_me()).username)}",
        text=out,
    )
    return page["url"]


def code(data):
    OK.update({len(OK): data})
    return str(len(OK) - 1)


def decode(key):
    if OK.get(int(key)):
        return OK[int(key)]
    return


async def qclean():
    try:
        os.system("rm downloads/*")
        os.system("rm encode/*")
        for proc in psutil.process_iter():
            processName = proc.name()
            processID = proc.pid
            print(processName, " - ", processID)
            if processName == "ffmpeg":
                os.kill(processID, signal.SIGKILL)
    except Exception:
        pass


async def skip(e):
    if (
        str(e.query.user_id) not in OWNER
        and e.query.user_id != DEV
        and str(e.query.user_id) not in str(USER_MAN[0])
    ):
        ans = "You're not allowed to do this!"
        return await e.answer(ans, cache_time=0, alert=False)
    wah = e.pattern_match.group(1).decode("UTF-8")
    wh = decode(wah)
    out, dl, id = wh.split(";")
    try:
        # if QUEUE.get(int(id)):
        if QUEUE.get(id):
            WORKING.clear()
            # QUEUE.pop(int(id))
            QUEUE.pop(id)
            await save2db()
        ans = "Cancelling encoding please wait…"
        await e.answer(ans, cache_time=0, alert=False)
        await e.delete()
        os.remove(dl)
        os.remove(out)
        # Lets kill ffmpeg else it will run in memory even after deleting
        # input.
        for proc in psutil.process_iter():
            processName = proc.name()
            processID = proc.pid
            print(processName, " - ", processID)
            if processName == "ffmpeg":
                os.kill(processID, signal.SIGKILL)
    except BaseException:
        pass
    return


async def fast_download(e, download_url, filename=None):
    def progress_callback(d, t):
        return (
            asyncio.get_event_loop().create_task(
                progress(
                    d,
                    t,
                    e,
                    time.time(),
                    f"Downloading from {download_url}",
                )
            ),
        )

    async def _maybe_await(value):
        if inspect.isawaitable(value):
            return await value
        else:
            return value

    async with aiohttp.ClientSession() as session:
        async with session.get(download_url, timeout=None) as response:
            if not filename:
                filename = download_url.rpartition("/")[-1]
            filename = os.path.join("downloads", filename)
            total_size = int(response.headers.get("content-length", 0)) or None
            downloaded_size = 0
            with open(filename, "wb") as f:
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        await _maybe_await(
                            progress_callback(downloaded_size, total_size)
                        )
            return filename
