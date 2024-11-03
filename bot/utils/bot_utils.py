import os
import zlib
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from re import match as re_match

import requests
from aiohttp import ClientSession

from bot import (
    LOGS,
    asyncio,
    caption_file,
    dt,
    ffmpeg_file,
    ffmpeg_file2,
    ffmpeg_file3,
    ffmpeg_file4,
    filter_file,
    itertools,
    tele,
    telegraph_errors,
    tgp_author,
    tgp_author_url,
    tgp_client,
    time,
)
from bot.config import _bot, conf

OK = {}
suffix = conf.CMD_SUFFIX


def add_temp_user(id):
    _bot.temp_users.append(id)


def bot_is_paused():
    if _bot.paused:
        return True


def u_cancelled():
    return _bot.u_cancel


def enc_canceller():
    return _bot.e_cancel


def get_f():
    if not Path(filter_file).is_file():
        return
    with open(filter_file, "r") as file:
        _f = file.read().strip()
    return _f


def get_bqueue():
    return _bot.batch_queue


def get_preview(list=False):
    return _bot.preview_batch if not list else _bot.preview_list


def get_previewer():
    return _bot.batch_ing[0] if _bot.batch_ing else None


def get_queue():
    return _bot.queue


def get_pause_status():
    return _bot.paused[0] if _bot.paused else None


def get_aria2():
    return _bot.aria2


def get_var(var):
    var_dict = dict()
    var_dict.update(
        {
            "groupenc": _bot.groupenc,
            "version2": _bot.version2,
            "paused": _bot.paused,
        }
    )
    return var_dict.get(var.casefold())


def get_v():
    return _bot.version2[0] if _bot.version2 else None


def if_queued():
    if _bot.queue:
        return True


def pause(unpause=False, status=1):
    return _bot.paused.clear() if unpause else _bot.paused.append(status)


async def rm_pause(match=None, time=0):
    if bot_is_paused():
        if match and match == get_pause_status():
            await asyncio.sleep(time)
            pause(unpause=True)
        elif not match:
            await asyncio.sleep(time)
            pause(unpause=True)


def rm_temp_user(id):
    _bot.temp_users.remove(id)


class Qbit_c:
    def __init__(self, count=None, flist=None, error=None):
        self.count = count
        self.file_list = flist
        self.error = error
        self.hash = None
        self.name = None

    def __str__(self):
        return self.error or self.name


class Encode_info:
    def __init__(self):
        self.previous = None
        self.reset()

    def __str__(self):
        return self.current

    def reset(self):
        self.current = None
        self.batch = False
        self.cached_dl = False
        self.qbit = False
        self.select = None
        self.uri = None
        self._current = None


encode_info = Encode_info()


class Encode_job:
    def __init__(self):
        self.reset(force=True)

    class Jobs:
        def __init__(self):
            self.f1 = True
            self.f2 = Path(ffmpeg_file2).is_file()
            self.f3 = Path(ffmpeg_file3).is_file()
            self.f4 = Path(ffmpeg_file4).is_file()

    def jobs(self, list=False):
        job = []
        for x in (self.ins.f1, self.ins.f2, self.ins.f3, self.ins.f4):
            job.append(x) if x else None
        if list:
            return job
        return len(job)

    def done(self):
        if self.ins.f1:
            self.ins.f1 = None
        elif self.ins.f2:
            self.ins.f2 = None
        elif self.ins.f3:
            self.ins.f3 = None
        elif self.ins.f4:
            self.ins.f4 = None

    def get_pending_index(self):
        if self.ins.f1:
            return 1
        elif self.ins.f2:
            return 2
        elif self.ins.f3:
            return 3
        elif self.ins.f4:
            return 4

    def get_pending_pos(self):
        if self.ins.f1:
            return
        elif self.ins.f2:
            return "2nd"
        elif self.ins.f3:
            return "3rd"
        elif self.ins.f4:
            return "4th"

    def pending(self):
        if self.ins.f1:
            return ffmpeg_file
        elif self.ins.f2:
            return ffmpeg_file2
        elif self.ins.f3:
            return ffmpeg_file3
        elif self.ins.f4:
            return ffmpeg_file4

    def reset(self, force=False):
        if not force and self.busy:
            return
        self.ins = self.Jobs()
        self.busy = False
        self.id = None
        self.prev_dl_client = None


encode_job = Encode_job()


sdict = dict()
sdict.update(
    {
        3: "Not a video.",
        2: "DONE!",
        1: "✅",
        0: "❌",
        None: "NOT SET!",
    }
)


THREADPOOL = ThreadPoolExecutor(max_workers=1000)
MAGNET_REGEX = r"magnet:\?xt=urn:[a-z0-9]+:[a-zA-Z0-9]{32}"
URL_REGEX = r"^(https?://|ftp://)?(www\.)?[^/\s]+\.[^/\s:]+(:\d+)?(/[^?\s]*[\s\S]*)?(\?[^#\s]*[\s\S]*)?(#.*)?$"
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


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


def is_magnet(magnet_link):
    return bool(re_match(MAGNET_REGEX, magnet_link))


def is_url(url):
    url = re_match(URL_REGEX, url)
    return bool(url)


def replace_proxy(url):
    file = "replace_proxy.txt"
    if not (url and Path(file).is_file()):
        return url
    with open(file, "r") as file:
        rep_proxies = file.read().splitlines()
    for rep_proxy in rep_proxies:
        if not (rep_proxy and len(rep_proxy.split()) > 1):
            return url
        d_search, proxy = rep_proxy.split()
        if not url.startswith(d_search):
            continue
        if proxy.endswith("="):
            url = f"{proxy}{url}"
        else:
            url = url.replace(d_search, proxy)
        break
    return url


def check_cmds(command: str, *matches: str):
    def check_cmd(command: str, match: str):
        match += suffix
        c = command.split(match, maxsplit=1)
        return len(c) == 2 and not c[1]

    for match in matches:
        if check_cmd(command, match):
            return True
    return False


def gfn(fn):
    "gets module path"
    return ".".join([fn.__module__, fn.__qualname__])


def string_escape(s: str, encoding="utf-8"):
    "unescape escaped characters in string"
    # https://stackoverflow.com/questions/14820429/how-do-i-decodestring-escape-in-python-3
    return (
        (
            s.encode("latin1")  # To bytes, required by 'unicode-escape'
            # Perform the actual octal-escaping decode
            .decode("unicode-escape")
            .encode("latin1")  # 1:1 mapping back to bytes
            .decode(encoding)
        )
        if s
        else s
    )


def list_to_str(lst: list, sep=" ", start: int = None, md=True):
    string = str()
    t_start = start if isinstance(start, int) else 1
    for i, count in zip(lst, itertools.count(t_start)):
        if start is None:
            string += str(i) + sep
            continue
        entry = f"`{i}`"
        string += f"{count}. {entry} {sep}"

    return string.rstrip(sep)


def txt_to_str(txt: str):
    if Path(txt).is_file():
        with open(txt, "r") as file:
            string = file.read().strip()
            file.close()
    else:
        string = None
    return string


def is_audio_file(filename: str):
    audio_file_extensions = (
        ".aac",
        ".mp3",
        ".m4a",
        ".flac",
        ".opus",
        ".wav",
    )
    if filename.endswith((audio_file_extensions)):
        return True


def is_subtitle_file(filename: str):
    sub_file_extensions = (
        ".ass",
        ".srt",
        ".txt",
        ".pgs",
    )
    if filename.endswith((sub_file_extensions)):
        return True


def is_video_file(filename: str):
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


def is_supported_file(filename: str):
    for support in (is_audio_file, is_subtitle_file, is_video_file):
        if support(filename):
            return True
    return False


def get_readable_file_size(size_in_bytes: int) -> str:
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f"{round(size_in_bytes, 2)}{SIZE_UNITS[index]}"
    except IndexError:
        return "File too large"


async def get_html(link):
    async with ClientSession(trust_env=True) as session:
        async with session.get(replace_proxy(link)) as res:
            return await res.text()


def create_api_token(retries=10):
    telgrph_tkn_err_msg = "Couldn't not successfully create telegraph api token!."
    while retries:
        try:
            tgp_client.create_api_token("Mediainfo")
            break
        except (requests.exceptions.ConnectionError, ConnectionError) as e:
            retries -= 1
            if not retries:
                LOGS.info(telgrph_tkn_err_msg)
                break
            time.sleep(1)
    return retries


async def post_to_tgph(title, out):
    author = tgp_author or ((await tele.get_me()).first_name)
    author_url = (
        f"https://t.me/{((await tele.get_me()).username)}"
        if not (tgp_author_url and is_url(tgp_author_url))
        else tgp_author_url
    )

    retries = 10
    while retries:
        try:
            page = await sync_to_async(
                tgp_client.post,
                title=title,
                author=author,
                author_url=author_url,
                text=out,
            )
            return page
        except telegraph_errors.APITokenRequiredError as e:
            result = await sync_to_async(create_api_token)
            if not result:
                raise e
        except (requests.exceptions.ConnectionError, ConnectionError) as e:
            retries -= 1
            if not retries:
                raise e
            await asyncio.sleep(1)


def get_filename(message):
    media_type = str(message.media)
    if media_type == "MessageMediaType.VIDEO":
        doc = message.video
    else:
        doc = message.document
    mcap = message.caption
    mpcap = None if mcap and "\n" in mcap else mcap
    file_name = mpcap if mpcap and not Path(caption_file).is_file() else doc.file_name
    if not file_name:
        file_name = "video_" + dt.now().isoformat("_", "seconds") + ".mp4"
    root, ext = os.path.splitext(file_name)
    file_name = root + ".mkv" if not ext else file_name

    return file_name


async def split_text(text: str, split="\n", pre=False):
    current_list = ""
    list_size = 4000
    message_list = []
    for string in text.split(split):
        line = string + split if not pre else split + string
        if len(current_list) + len(line) <= list_size:
            current_list += line
        else:
            # Add current_list to account_list
            message_list.append(current_list)
            # Reset the current_list with a new "line".
            current_list = line
    # Add the last line into list.
    message_list.append(current_list)
    return message_list


def code(data, infile=None, outfile=None, user=None, stime=None, index=None):
    if not index:
        OK.update({len(OK): data})
        return str(len(OK) - 1)
    OK.update({index: (data, infile, outfile, user, stime)})
    return


# def code(data):
# OK.update({len(OK): data})
# return str(len(OK) - 1)


def decode(key: str | int, pop=False):
    key = int(key) if isinstance(key, str) and key.isdigit() else key
    if pop:
        return OK.pop(key)
    return OK.get(key)


def value_check(value):
    if not value:
        return "-"
    return value


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


def hbs(size: int):
    if not size:
        return ""
    power = 2**10
    raised_to_pow = 0
    dict_power_n = {0: "B", 1: "K", 2: "M", 3: "G", 4: "T", 5: "P"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


async def crc32(filename: str, chunksize=65536):
    """Compute the CRC-32 checksum of the contents of the given filename"""
    with open(filename, "rb") as f:
        checksum = 0
        while chunk := f.read(chunksize):
            checksum = zlib.crc32(chunk, checksum)
        return "%X" % (checksum & 0xFFFFFFFF)


async def get_codec(file="ffmpeg.txt"):
    """Get file codec from ffmpeg encoding parameters"""
    with open(file, "r") as file:
        ff_code = file.read().rstrip()
        file.close()
    s_check = dict()
    __out = ""
    s_check.update(
        {
            "360": "360p",
            "480": "480p",
            "720": "720p",
            "1080": "1080p",
            "x264": "AVC",
            "x265": "HEVC",
            "libsvtav1": "AV1",
            "svt_av1": "AV1",
        }
    )
    for key, value in s_check.items():
        if key in ff_code:
            __out += f"[{value}] "
    return __out.strip()


async def auto_rename(
    parsed_name: str, original_name: str, refunc: str, caption=False, general=False
) -> str:
    """
    Auto-rename file/caption name, if it matches given string or list of strings seperated by newlines
    """
    out_name = ""
    caption = True if general else caption
    if refunc:
        for ren in refunc.split("\n"):
            ren = ren.strip()
            de_name = ren.split("|")[0].strip()
            re_name = ren.split("|")[1].strip()
            if original_name.casefold() == de_name.casefold():
                out_name = re_name
            else:
                continue
            if caption and len(ren.split("|")) > 2:
                cap_name = ren.split("|")[2].strip()
                if str(cap_name) == "0":
                    out_name = parsed_name
                elif str(cap_name) == "1":
                    out_name = re_name
                else:
                    out_name = cap_name
            if general:
                if len(ren.split("|")) > 3:
                    key = ren.split("|")[2].strip()
                    if str(key) == "00":
                        return False, original_name
                    elif str(key) == "0":
                        return False, out_name
                    elif str(key) == "1":
                        return True, out_name
                    else:
                        return True, key
                else:
                    return True, original_name

    if general:
        return True, original_name
    if not out_name:
        out_name = parsed_name
    elif str(out_name) == "00":
        out_name = original_name
    return out_name


async def text_filter():
    """Read three filter (.txt) files and returns the contents"""
    nft = Path("Namefilter.txt")
    rft = Path("Releasefilter.txt")
    rct = Path("Release_caption.txt")

    if nft.is_file():
        with open("Namefilter.txt", "r") as file:
            nf = file.read().strip()
            file.close()
    else:
        nf = None
    if rft.is_file():
        with open("Releasefilter.txt", "r") as file:
            rf = file.read().strip()
            file.close()
    else:
        rf = None
    if rct.is_file():
        with open("Release_caption.txt", "r") as file:
            rc = file.read().strip()
            file.close()
    else:
        rc = None
    return nf, rf, rc


async def sync_to_async(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(THREADPOOL, pfunc)
    return await future if wait else future
