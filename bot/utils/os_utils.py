import asyncio
import json
import os
import pickle
import sys
from pathlib import Path
from subprocess import run as bashrun

import anitopy
import psutil
from html_telegraph_poster import TelegraphPoster

from bot import (
    DATABASE_URL,
    TELEGRAPH_API,
    TELEGRAPH_AUTHOR,
    signal,
    tele,
    version_file,
)

from .bot_utils import TEMP_USERS, get_queue, list_to_str
from .log_utils import log, logger


async def enshell(cmd):
    # Create a subprocess and wait for it to finish
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    # Return the output of the command and the process object
    return (process, stdout.decode(), stderr.decode())


async def is_running(proc):
    # with contextlib.suppress(asyncio.TimeoutError):
    # await asyncio.wait_for(proc.wait(), 1e-6)
    await asyncio.sleep(1e-6)
    return proc.returncode is None


async def info(file):
    try:
        author = (
            TELEGRAPH_AUTHOR.split("|")[0]
            if TELEGRAPH_AUTHOR and TELEGRAPH_AUTHOR.casefold != "auto"
            else None
        )
        author_url = (
            TELEGRAPH_AUTHOR.split("|")[1]
            if TELEGRAPH_AUTHOR and len(TELEGRAPH_AUTHOR.split("|")) > 1
            else None
        )
        author = ((await tele.get_me()).first_name) if not author else author
        author_url = (
            f"https://t.me/{((await tele.get_me()).username)}"
            if not author_url
            else author_url
        )

        # process = subprocess.Popen(
        # ["mediainfo", file, "--Output=HTML"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.STDOUT,
        # )
        cmd = f'mediainfo """{file}""" --Output=HTML'
        proc, stdout, stderr = await enshell(cmd)
        if stderr and not stdout:
            raise Exception(stderr)
        else:
            out = stdout
        client = TelegraphPoster(use_api=True, telegraph_api_url=TELEGRAPH_API)
        client.create_api_token("Mediainfo")
        page = client.post(
            title="Mediainfo",
            author=author,
            author_url=author_url,
            text=out,
        )
        return page["url"]
    except Exception:
        await logger(Exception)


def p_dl(link, pic):
    return os.system(f"wget {link} -O {pic}")


def check_ext(path, ext=".mkv", get_split=False):
    """Checks path and if no extension is found and or given, defaults to 'mkv'."""
    root, ext_ = os.path.splitext(path)
    if not ext_:
        path = root + ext
    else:
        ext = ext_
    if get_split:
        return path, root, ext
    return path


def s_remove(*filenames):
    """Deletes a single or tuple of files silently and return no errors if not found"""
    for filename in filenames:
        try:
            os.remove(filename)
        except OSError:
            pass


async def parse_dl(path):
    if not path:
        return None
    _dir, filename = os.path.split(path)
    parsed = anitopy.parse(filename)
    final = f"\n\n**Video/file information:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**"
    if parsed:
        for key, value in parsed.items():
            final += f"\n**{key}:** `{value}`"
    return final


def kill_process(process):
    try:
        for proc in psutil.process_iter():
            processName = proc.name()
            processID = proc.pid
            print(processName, " - ", processID)
            if processName == process:
                os.kill(processID, signal.SIGKILL)
    except Exception:
        pass


async def qclean():
    try:
        os.system("rm downloads/*")
        os.system("rm downloads2/*")
        os.system("rm encode/*")
        os.system("rm thumb/*")
        kill_process("ffmpeg")
    except Exception:
        pass


async def updater(msg=None):
    try:
        with open(version_file, "r") as file:
            ver = file.read()
        await qclean()
        os.system("touch update")
        bashrun(["python3", "update.py"])
        with open(version_file, "r") as file:
            ver2 = file.read()

        if ver != ver2:
            vmsg = True
        else:
            vmsg = False

        if not DATABASE_URL:
            with open("local_queue.pkl", "wb") as file:
                pickle.dump(get_queue(), file)
            with open("t_users.pkl", "wb") as file:
                pickle.dump(list_to_str(TEMP_USERS), file)

        if msg:
            message = str(msg.chat.id) + ":" + str(msg.id)
            os.execl(
                sys.executable, sys.executable, "-m", "bot", f"update {vmsg}", message
            )
        else:
            os.execl(sys.executable, sys.executable, "-m", "bot")
    except Exception:
        await logger(Exception)


async def get_stream_info(file):
    try:
        if not Path(file).is_file():
            return None, None
        out = await enshell(
            f'ffprobe -hide_banner -show_streams -print_format json """{file}"""'
        )
        details = json.loads(out[1])
        a_lang = ""
        s_lang = ""
        for stream in details["streams"]:
            stream["index"]
            try:
                stream["codec_name"]
            except BaseException:
                continue
            stream_type = stream["codec_type"]
            if stream_type not in ("audio", "subtitle"):
                continue
            if stream_type == "audio":
                try:
                    a_lang += stream["tags"]["language"] + "|"
                except BaseException:
                    a_lang += "?|"
            elif stream_type == "subtitle":
                try:
                    s_lang += stream["tags"]["language"] + "|"
                except BaseException:
                    s_lang += "?|"
    except KeyError as k_e:
        if not str(k_e) == "'streams'":
            await logger(Exception)
        else:
            return None, None
            log("[NOTICE] No stream was found.")
    except Exception:
        await logger(Exception)
    return (a_lang.strip("|"), s_lang.strip("|"))


async def pos_in_stm(file, lang1="eng", lang2="eng-us", get="both"):
    try:
        if not (Path(file)).is_file():
            return None, None
        a_pos = ""
        s_pos = ""
        _ainfo, _sinfo = await get_stream_info(Path(file))
        i = 0
        for audio in _ainfo.split("|"):
            if audio == lang1 or audio == lang2:
                a_pos = i
                break
            i = i + 1
        i = 0
        for subs in _sinfo.split("|"):
            if subs == lang1 or audio == lang2:
                s_pos = i
            i = i + 1
    except Exception:
        await logger(Exception)
    if get.casefold() == "a" or get.casefold() == "audio":
        return a_pos
    if get.casefold() == "s" or get.casefold() == "sub":
        return s_pos
    return a_pos, s_pos


def dir_exists(folder):
    return os.path.isdir(folder)


def x_or_66():
    os.system("kill -9 -1")


async def re_x(i, msg):
    await qclean()
    os.execl(sys.executable, sys.executable, "-m", "bot", i, msg)


def file_exists(file):
    return Path(file).is_file()


def size_of(file):
    return int(Path(file).stat().st_size)
