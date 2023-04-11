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
    sender = str(event.sender_id)
    currentTime = get_readable_time(time.time() - botStartTime)
    msg = ""
    msg1 = f"Hi `{event.sender.first_name}`\n"
    msg2 = f"{msg1}I've been alive for `{currentTime}` and i'm ready to encode videos 😗"
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    priv = await app.get_users(OWNER.split()[0])
    msg4 = f"{msg1}You're not allowed access to this bot\nAsk [{priv.first_name}](tg://user?id={OWNER.split()[0]}) (nicely) to grant you access."
    if sender not in OWNER:
        if sender not in TEMP_USERS:
            msg = msg4
        else:
            msg = msg3
        if event.is_private:
            yo = await event.reply("Nice try!")
            await asyncio.sleep(3)
            await yo.delete()
            return await event.delete()
    if not msg:
        msg = msg2
    await event.reply(
        msg,
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
        "**👘 An Encode bot**\n\n+This Bot Encode Videos With your custom ffmpeg or handbrake-cli settings.\n+Easy to Use (Depends)\n-Due to your custom Settings & hosting server bot may or may not take time to encode.\n\n\nJust Forward a Video or videos"
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


async def temp_unauth(event):
    sender = str(event.sender_id)
    error = "Failed!,\nCan't remove from temporarily allowed users"
    if sender not in OWNER:
        return event.reply("Nope")
    if event.is_reply:
        rep_event = await event.get_reply_message()
        new_id = rep_event.sender_id
    else:
        args = event.pattern_match.group(1)
        if args is not None:
            args = args.strip()
            if args.isdigit():
                new_id = args
            else:
                return await event.reply(
                    f"What do you mean by  `{args}` ?\nneed help? send /unauth"
                )
        else:
            return await event.reply(
                "Either reply to a message sent by the user you want to remove from temporarily allowed users or send /unauth (user-id)\nExample:\n  /unauth 123456"
            )
    new_id = str(new_id)
    if new_id == sender:
        return await event.reply("Why, oh why did you try to unpermit yourself?")
    if new_id in OWNER:
        return await event.reply(f"{error} because user is already a privileged user")
    if new_id not in TEMP_USERS:
        return await event.reply(
            f"{error} because user is not in the temporary allowed user list"
        )
    try:
        new_user = await app.get_users(new_id)
        new_user = new_user.first_name
    except Exception:
        new_user = new_id
    TEMP_USERS.remove(new_id)
    await save2db2(tusers, list_to_str(TEMP_USERS))
    return await event.reply(
        f"Removed `{new_user}` from temporarily allowed users {enmoji()}"
    )


async def temp_auth(event):
    sender = str(event.sender_id)
    error = "Failed!,\nCan't add to temporarily allowed users"
    if sender not in OWNER:
        return event.reply("Nope")
    if event.is_reply:
        rep_event = await event.get_reply_message()
        new_id = rep_event.sender_id
    else:
        args = event.pattern_match.group(1)
        if args is not None:
            args = args.strip()
            if args.isdigit():
                new_id = args
            else:
                return await event.reply(
                    f"What do you mean by  `{args}` ?\nneed help? send /auth"
                )
        else:
            return await event.reply(
                "Either reply to a message sent by the user you want to add to temporarily allowed users or send /auth (user-id)\nExample:\n  /auth 123456"
            )
    new_id = str(new_id)
    if new_id == sender:
        return await event.reply("Why, oh why did you try to permit yourself?")
    if new_id in OWNER:
        return await event.reply(f"{error} because user is already a privileged user")
    if new_id in TEMP_USERS:
        return await event.reply(f"{error} because user is already added")
    try:
        new_user = await app.get_users(new_id)
        new_user = new_user.first_name
    except Exception:
        new_user = new_id
    TEMP_USERS.append(new_id)
    await save2db2(tusers, list_to_str(TEMP_USERS))
    return await event.reply(
        f"Added `{new_user}` to temporarily allowed users {enmoji()}"
    )
