import asyncio
import json
import os
import shutil
import sys
from os import cpu_count
from pathlib import Path
from subprocess import run as bashrun

import anitopy
import psutil
import pymediainfo

from bot import ffmpeg_file, signal, version_file

from .bot_utils import post_to_tgph, sync_to_async
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


async def info(file, full=False):
    try:
        out = await sync_to_async(
            pymediainfo.MediaInfo.parse, file, output="HTML", full=full
        )
        if len(out) > 65536:
            out = (
                out[:65430]
                + "<strong>...<strong><br><br><strong>(TRUNCATED DUE TO CONTENT EXCEEDING MAX LENGTH)<strong>"
            )
        page = await post_to_tgph("MediaInfo", out)
        return page["url"]
    except Exception:
        await logger(Exception)


def p_dl(link, pic):
    return os.system(f"wget {link} -O {pic}")


def check_ext(path, ext=".mkv", get_split=False, overide=False):
    """Checks path and if no extension is found and or given, defaults to 'mkv'."""
    root, ext_ = os.path.splitext(path)
    if not ext_ or overide:
        path = root + ext
    else:
        ext = ext_
    if get_split:
        return path, root, ext
    return path


def s_remove(*filenames, folders=False):
    """Deletes a single or tuple of files silently and return no errors if not found"""
    if folders:
        for _dir in filenames:
            try:
                shutil.rmtree(_dir)
            except Exception:
                pass
        return
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
        os.system("rm -rf downloads/*")
        os.system("rm -rf downloads2/*")
        os.system("rm -rf encode/*")
        os.system("rm -rf mux/*")
        os.system("rm minfo/*")
        try:
            with open(ffmpeg_file, "r") as file:
                ffmpeg = file.read().rstrip().split()[0]
            await sync_to_async(kill_process, ffmpeg)
        except Exception:
            await logger(Exception)
    except Exception:
        pass


async def updater(msg=None):
    try:
        with open(version_file, "r") as file:
            ver = file.read()
        await qclean()
        Path("update").touch()
        bashrun([sys.executable, "update.py"])
        with open(version_file, "r") as file:
            ver2 = file.read()

        if ver != ver2:
            vmsg = True
        else:
            vmsg = False

        if msg:
            message = str(msg.chat.id) + ":" + str(msg.id)
            os.execl(
                sys.executable, sys.executable, "-m", "bot", f"update {vmsg}", message
            )
        else:
            os.execl(sys.executable, sys.executable, "-m", "bot")
    except Exception:
        await logger(Exception)


def read_n_to_last_line(filename, n=1):
    """Returns the nth before last line of a file (n=1 gives last line)"""
    num_newlines = 0
    with open(filename, "rb") as f:
        try:
            f.seek(-2, os.SEEK_END)
            while num_newlines < n:
                f.seek(-2, os.SEEK_CUR)
                if f.read(1) == b"\n":
                    num_newlines += 1
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line


async def get_stream_duration(file):
    if not Path(file).is_file():
        return
    result = 0
    try:
        out = await enshell(
            f'ffprobe -hide_banner -show_streams -show_format -print_format json """{file}"""'
        )
        details = json.loads(out[1])
        result = round(float(details.get("format").get("duration")))
    except Exception:
        await logger(Exception)
    finally:
        return result


async def get_video_thumbnail(file, output="thumb2.jpg", with_dur=False):
    try:
        duration = await get_stream_duration(file)
        if not duration:
            return
        if duration == 0:
            duration = 3
        tduration = duration // 2
        out = await enshell(
            f'ffmpeg -hide_banner -loglevel error -ss {tduration} -i """{file}""" -vf thumbnail -q:v 1 -frames:v 1 -threads {cpu_count() // 2} {output} -y'
        )
        if not file_exists(output):
            return None
        if with_dur:
            return (output, duration)
        return output
    except Exception:
        await logger(Exception)


async def get_stream_info(file):
    try:
        if not Path(file).is_file():
            return None, None
        if Path(file + ".aria2").is_file():
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
        _ainfo, _sinfo = await get_stream_info(file)
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
