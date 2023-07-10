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

import aria2p
from pymongo import MongoClient
from quote import quote
from random_word import RandomWords

from . import *
from .config import *

DOCKER_DEPLOYMENT = []
DISPLAY_DOWNLOAD = []
UNLOCK_UNSTABLE = []
QUEUE_STATUS = []
CACHE_QUEUE = []
USER_MAN = []
GROUPENC = []
LOCKFILE = []
VERSION2 = []
E_CANCEL = []
U_CANCEL = []
R_QUEUE = []
STARTUP = []
WORKING = []
EVENT2 = []
ARIA2 = []

QUEUE = {}
OK = {}

FINISHED_PROGRESS_STR = "🧡"
UN_FINISHED_PROGRESS_STR = "🤍"
MAX_MESSAGE_LENGTH = 4096
URL_REGEX = r"^(https?://|ftp://)?(www\.)?[^/\s]+\.[^/\s:]+(:\d+)?(/[^?\s]*[\s\S]*)?(\?[^#\s]*[\s\S]*)?(#.*)?$"

uptime = dt.now()
global aria2
aria2 = None
# os.system(
#    "curl -sL https://raw.githubusercontent.com/anasty17/mirror-leech-telegram-bot/master/aria.sh|bash"
# )

if EABF:
    UNLOCK_UNSTABLE.append(1)

if THUMB:
    os.system(f"wget {THUMB} -O thumb.jpg")

if DL_STUFF:
    for link in DL_STUFF.split(","):
        os.system(f"wget {link.strip()}")

if LOCK_ON_STARTUP:
    LOCKFILE.append(1)

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
if not os.path.isdir("dump/"):
    os.mkdir("dump/")
if not os.path.isdir("thumb/"):
    os.mkdir("thumb/")


if os.path.isdir("/tgenc"):
    DOCKER_DEPLOYMENT.append(1)

if TEMP_USERS:
    TEMP_USERS = TEMP_USERS.split()


def load_db(_db, file):
    queries = _db.find({})
    for query in queries:
        que = query["queue"]
        que = que[0]
        io = StringIO(que)
        pre = json.load(io)
        if len(pre) > 5:
            file = open(file, "w")
            file.write(str(pre) + "\n")
            file.close()


if DATABASE_URL:
    cluster = MongoClient(DATABASE_URL)
    db = cluster[DBNAME]
    queue = db["queue"]
    ffmpegdb = db["code"]
    filterz = db["filter"]
    namedb = db["autoname"]
    tusers = db["tempusers"]
    queries = queue.find({})
    for query in queries:
        que = str(query["queue"])
        io = StringIO(que)
        pre = json.load(io)
        QUEUE.update(pre)
    queries = tusers.find({})
    for query in queries:
        que = query["queue"]
        que = que[0]
        io = StringIO(que)
        pre = json.load(io)

        if len(pre) > 5:
            for i in pre.split():
                if str(i) in TEMP_USERS:
                    continue
                TEMP_USERS.append(i)

    load_db(ffmpegdb, "ffmpeg.txt")
    load_db(filterz, "filter.txt")
    load_db(namedb, "Auto-rename.txt")

else:
    ffmpegdb = ""
    filterz = ""
    namedb = ""
    tusers = ""


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


def list_to_str(lst, e=" ", n=None):
    string = ""
    for i in lst:
        if n:
            string += f"{n}. {i}{e}"
            n = n + 1
        else:
            string += str(i) + e

    if n:
        return n, string
    else:
        return string


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


async def start_aria2p():
    try:
        globals()["aria2"] = aria2p.API(
            aria2p.Client(host="http://localhost", port=6800, secret="")
        )
        aria2.add(
            "https://nyaa.si/download/1690208.torrent",
            {"dir": f"{os.getcwd()}/downloads"},
        )
        await asyncio.sleep(2)
        downloads = aria2.get_downloads()
        await asyncio.sleep(3)
        aria2.remove(downloads, force=True, files=True, clean=True)
        ARIA2.append(aria2)

        # return aria2

    except Exception:
        ers = traceback.format_exc()
        LOGS.critical(ers)
        await channel_log("An error occurred while starting aria2p")
        await channel_log(ers)

        # return None


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
            msg = await bot.send_message(
                log,
                f"**#ERROR\n\n⛱️ Summary of what happened:**\n`{error}`\n\nTo restict error messages to logs set the EABF vars to False. {enmoji()}",
            )
        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)
            LOGS.info(error)
            msg = ""
        return msg


async def q_dup_check(event):
    try:
        if QUEUE_STATUS:
            check = True
            for q_id in QUEUE_STATUS:
                _q_id = str(event.chat_id) + " " + str(event.id)
                if q_id == _q_id:
                    check = False
        else:
            check = True
    except Exception:
        check = True
        er = traceback.format_exc()
        LOGS.info(er)
        await channel_log(er)
    return check


async def get_cached(dl, sender, user, e, op):
    try:
        dl_check = Path(dl)
        dl_check2 = Path(dl + ".temp")
        if dl_check.is_file():
            await e.edit("`Using cached download…`")
            if op:
                await op.edit("`Using cached download…`")
            await asyncio.sleep(3)
        if dl_check2.is_file():
            prog_msg = f"{enmoji()} Waiting for download to complete"
            false_prog = "..."
            while dl_check2.is_file():
                try:
                    false_prog = "..." if len(false_prog) > 20 else false_prog
                    await e.edit("`" + prog_msg + false_prog + "`")
                    if op:
                        await asyncio.sleep(3)
                        await op.edit(
                            f"{enmoji()} `Waiting for` [{sender.first_name}'s](tg://user?id={user}) `download to complete{false_prog}`"
                        )
                    false_prog += "."
                    await asyncio.sleep(15)
                except errors.rpcerrorlist.MessageNotModifiedError:
                    await asyncio.sleep(15)
                    continue
                except errors.FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    continue
        CACHE_QUEUE.clear()
        if not dl_check.is_file():
            raise Exception("Getting cached file failed\nfile might have been deleted.")
        return True
    except Exception:
        er = traceback.format_exc()
        LOGS.info(er)
        await channel_log(er)
        await e.edit("`Using cached download failed\nRe-downloading…`")
        if op:
            await op.edit("`Using cached download failed\nRe-downloading…`")
        CACHE_QUEUE.clear()
        return False


async def enpause(message):
    pause_msg = " `Bot has been paused to continue, unlock bot using the /lock command`"
    while LOCKFILE:
        try:
            await message.edit(enmoji() + pause_msg)
            await asyncio.sleep(10)
        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except pyro_errors.BadRequest:
            await asyncio.sleep(10)
            continue
        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)
            await channel_log(ers)


async def fake_progress(leech_task, message):
    r_file = ""
    while leech_task.done() is not True:
        try:
            __file = Path("leech_log")
            if __file.is_file():
                with open(__file, "r") as file:
                    r_file = file.read().rstrip()
                    file.close()
                l_file = r_file.split("\n")
                if len(l_file) < 1:
                    await asyncio.sleep(4)
                    continue
                elif len(l_file) < 5:
                    i = -1
                else:
                    i = -5
                f_prog1 = "**Download Progress:**\n\n"
                f_prog2 = ""
                while i < 0:
                    f_prog2 += f"`{l_file[i]}`\n"
                    f_prog2 = f_prog2.replace("[ [1;32mNOTICE [0m]", f"{enmoji} INFO:")
                    f_prog2 = re.sub(r"#\w+\s*", "", f_prog2)
                    i = i + 1
                f_prog2 = "`Loading please wait…`" if not f_prog2 else f_prog2
                f_prog = f_prog1 + f_prog2
            else:
                f_prog = f"**Well that ain't right** {enmoji2()}"
            await message.edit(f_prog)
            await asyncio.sleep(15)
        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except pyro_errors.BadRequest:
            await asyncio.sleep(10)
            continue
        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)
            await channel_log(ers)
            break
    if r_file:
        return r_file
    else:
        __file = Path("leech_log")
        if __file.is_file():
            with open(__file, "r") as file:
                r_file = file.read().rstrip()
                file.close()
            return r_file
        else:
            return "`What have you done?`"


def rm_leech_file(gid):
    try:
        download = aria2.get_download(gid)
        download.remove(force=True, files=True)
        if download.followed_by_ids:
            download = aria2.get_download(
                download.followed_by_ids[0]
            )
            download.remove(force=True, files=True)
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)


async def get_leech_name(url):
    try:
        downloads = aria2.add(url, {"dir": f"{os.getcwd()}/temp"})
        while True:
            download = aria2.get_download(downloads[0].gid)
            download = download.live
            if download.followed_by_ids:
                gid = download.followed_by_ids[0]
                download = aria2.get_download(gid)
            if download.status == "error":
                download_error = (
                    "E" + download.error_code + " :" + download.error_message
                )
                filename = "aria2_error " + download_error
                break
            if download.name.endswith(".torrent"):
                await asyncio.sleep(2)
                continue
            else:
                if is_video_file(download.name) is True:
                    filename = download.name
                else:
                    filename = ""
                break
        download.remove(force=True, files=True)
        if download.following_id:
            download = aria2.get_download(download.following_id)
            download.remove(force=True, files=True)
    except Exception:
        filename = None
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)
    return filename


async def start_rpc():
    try:
        os.system(
            "aria2c --enable-rpc=true --rpc-max-request-size=1024M --seed-time=0 --follow-torrent=mem --summary-interval=0 --daemon=true --allow-overwrite=true"
        )
        await asyncio.sleep(3)
        await start_aria2p()
    except Exception:
        ers = traceback.format_exc()
        LOGS.critical(ers)
        await channel_log(
            "A major error pertaining to aria2 occured and as such error cannot be recovered from do /restart to allow bot an attempt to fix.\ncheck below for details."
        )
        await channel_log()


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


class already_dl(Exception):
    pass


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


async def enshell(cmd):
    # Create a subprocess and wait for it to finish
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    # Return the output of the command and the process object
    return (process, stdout.decode(), stderr.decode())


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


def value_check(value):
    if not value:
        return "-"
    return value


def s_remove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


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
    msg = await e.get_message()
    try:
        # if QUEUE.get(int(id)):
        if QUEUE.get(id):
            WORKING.clear()
            # QUEUE.pop(int(id))
            QUEUE.pop(id)
            await save2db()
        ans = "Cancelling encoding please wait…"
        await e.answer(ans, cache_time=0, alert=False)
        if str(msg.chat_id) not in LOG_CHANNEL:
            await e.delete()
        s_remove(dl)
        s_remove(out)
        E_CANCEL.append(e.query.user_id)
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
