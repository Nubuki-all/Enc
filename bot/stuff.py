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

import os
import shutil
from pathlib import Path

import psutil

from .util import get_readable_file_size, get_readable_time
from .worker import *


async def up(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    stt = dt.now()
    ed = dt.now()
    v = ts(int((ed - uptime).seconds) * 1000)
    ms = (ed - stt).microseconds / 1000
    p = f"🌋Pɪɴɢ = {ms}ms"
    await event.reply(v + "\n" + p)


async def status(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    if os.path.exists(".git"):
        last_commit = subprocess.check_output(
            ["git log -1 --date=short --pretty=format:'%cd || %cr'"], shell=True
        ).decode()
    else:
        last_commit = "UNAVAILABLE!"
    verpre = Path("version.txt")
    if verpre.is_file():
        with open("version.txt", "r") as file:
            vercheck = file.read().strip()
            file.close()
    else:
        vercheck = "Tf?"
    currentTime = get_readable_time(time.time() - botStartTime)
    ostime = get_readable_time(time.time() - psutil.boot_time())
    swap = psutil.swap_memory()
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    p_cores = psutil.cpu_count(logical=False)
    t_cores = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/").percent
    await event.reply(
        f"**Version:** `{vercheck}`\n"
        f"**Commit Date:** `{last_commit}`\n\n"
        f"**Bot Uptime:** `{currentTime}`\n"
        f"**System Uptime:** `{ostime}`\n\n"
        f"**Total Disk Space:** `{total}`\n"
        f"**Used:** `{used}` "
        f"**Free:** `{free}`\n\n"
        f"**SWAP:** `{get_readable_file_size(swap.total)}`"
        f"** | **"
        f"**Used:** `{swap.percent}%`\n\n"
        f"**Upload:** `{sent}`\n"
        f"**Download:** `{recv}`\n\n"
        f"**Physical Cores:** `{p_cores}`\n"
        f"**Total Cores:** `{t_cores}`\n\n"
        f"**CPU:** `{cpuUsage}%` "
        f"**RAM:** `{memory.percent}%` "
        f"**DISK:** `{disk}%`\n\n"
        f"**Total RAM:** `{get_readable_file_size(memory.total)}`\n"
        f"**Used:** `{get_readable_file_size(memory.used)}` "
        f"**Free:** `{get_readable_file_size(memory.available)}`"
    )


async def start(event):
    if str(event.sender_id) not in OWNER:
        if event.is_private:
            yo = await event.reply("Nice try!")
            await asyncio.sleep(3)
            await yo.delete()
            return await event.delete()
    await event.reply(
        f"Hi `{event.sender.first_name}`\nThis is a bot that encodes Videos.\nOhh And It's For Personal Use Only! 😗",
        buttons=[
            [Button.inline("HELP", data="ihelp")],
            [
                Button.url("SOURCE (Original)", url="github.com/1Danish-00/"),
                Button.url("DEVELOPER", url="t.me/danish_00"),
            ],
            [Button.url("Maintainer ✌️", url="t.me/itsjust_r")],
        ],
    )


async def help(event):
    await event.reply(
        "**👘 An Encode bot**\n\n+This Bot Encode Videos With your custom ffmpeg or handbrake-cli settings.\n+Easy to Use (Depends)\n-Due to your custom Settings & hosting server bot may or may not take time to encode.\n\n\nJust Forward a Video…/videos"
    )


async def ihelp(event):
    await event.edit(
        "**⛩️ An Encode bot**\n\n+This Bot Encode Videos With your custom ffmpeg or handbrake-cli settings.\n+Easy to Use (Depends)\n-Due to your custom Settings & hosting server bot may or may not take time to encode.\n\n\nJust Forward a Video…/videos",
        buttons=[Button.inline("BACK", data="beck")],
    )


async def beck(event):
    await event.edit(
        f"Hi `{event.sender.first_name}`\nThis is bot that encodes Videos.\n\n",
        buttons=[
            [Button.inline("HELP", data="ihelp")],
            [
                Button.url("SOURCE (Original)", url="github.com/1Danish-00/"),
                Button.url("DEVELOPER", url="t.me/danish_00"),
            ],
            [Button.url("Maintainer ✌️", url="t.me/itsjust_r")],
        ],
    )
