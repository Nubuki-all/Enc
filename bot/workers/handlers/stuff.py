import os
import shutil
import time

import psutil

from bot import OWNER as owner
from bot import Button, botStartTime, dt, subprocess, version_file
from bot.fun.emojis import enmoji
from bot.utils.bot_utils import add_temp_user, get_readable_file_size, rm_temp_user
from bot.utils.bot_utils import time_formatter as tf
from bot.utils.db_utils import save2db2
from bot.utils.msg_utils import (
    pm_is_allowed,
    temp_is_allowed,
    user_is_allowed,
    user_is_owner,
)
from bot.utils.os_utils import file_exists


async def up(event, args, client):
    """ping function (deprecated)"""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    stt = dt.now()
    ed = dt.now()
    v = tf(time.time() - botStartTime)
    ms = (ed - stt).microseconds / 1000
    p = f"🌋Pɪɴɢ = {ms}ms"
    await event.reply(v + "\n" + p)


async def status(event, args, client):
    """Gets status of bot and server where bot is hosted.
    Requires no arguments."""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    if os.path.exists(".git"):
        last_commit = subprocess.check_output(
            ["git log -1 --date=short --pretty=format:'%cd || %cr'"], shell=True
        ).decode()
    else:
        last_commit = "UNAVAILABLE!"

    if file_exists(version_file):
        with open(version_file, "r") as file:
            vercheck = file.read().strip()
            file.close()
    else:
        vercheck = "Tf?"
    currentTime = tf(time.time() - botStartTime)
    ostime = tf(time.time() - psutil.boot_time())
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


async def start(event, args, client):
    """A function for the start command, accepts no arguments yet!"""
    currentTime = tf(time.time() - botStartTime)
    msg = ""
    msg1 = f"Hi `{event.sender.first_name}`\n"
    msg2 = f"{msg1}I've been alive for `{currentTime}` and i'm ready to encode videos 😗"
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    user = event.sender_id
    if not user_is_owner(user) and event.is_private:
        if not pm_is_allowed(in_pm=True):
            return await event.delete()
    if temp_is_allowed(user):
        msg = msg3
    elif not user_is_allowed(user) and not event.is_private:
        priv = await event.client.get_entity(owner.split()[0])
        msg = f"{msg1}You're not allowed access to this bot"
        msg += f"\nAsk [{priv.first_name}](tg://user?id={owner.split()[0]}) "
        msg += "(nicely) to grant you access."

    if not msg:
        msg = msg2
    await event.reply(
        msg,
        buttons=[
            [Button.inline("Help", data="ihelp")],
            [
                Button.url(
                    "Source-Code (Original)",
                    url="github.com/1Danish-00/compressorqueue",
                ),
                Button.url("Developer (Original)", url="t.me/danish_00"),
            ],
            [Button.url("Fork Maintainer", url="t.me/Col_serra")],
        ],
    )


async def help(event, args, client):
    return await start(event, args, client)


async def ihelp(event):
    await event.edit(
        "**⛩️ An Encode bot**\n\n+"
        "This bot encodes videos With your custom ffmpeg or handbrake-cli settings."
        "\n+Easy to Use (Depends)\n"
        "-Due to your custom Settings & hosting server bot may or may not take a long time to encode"
        ".\n\nJust Forward a Video…/videos"
        "\n\nFor available commands click the command button.",
        buttons=[
            [Button.inline("Commands", data="icommands")],
            [Button.inline("🔙 Back", data="beck")],
        ],
    )


async def beck(event):
    sender = event.query.user_id
    currentTime = tf(time.time() - botStartTime)
    msg = ""
    msg1 = f"Hi `{event.sender.first_name}`\n"
    msg2 = f"{msg1}I've been alive for `{currentTime}` and i'm ready to encode videos 😗"
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    if temp_is_allowed(sender):
        msg = msg3
    elif not user_is_allowed(sender):
        priv = await event.client.get_entity(owner.split()[0])
        msg = f"{msg1}You're not allowed access to this bot"
        msg += f"\nAsk [{priv.first_name}](tg://user?id={owner.split()[0]}) "
        msg += "(nicely) to grant you access."
    if not msg:
        msg = msg2
    await event.edit(
        msg,
        buttons=[
            [Button.inline("Help", data="ihelp")],
            [
                Button.url(
                    "Source-Code (Original)",
                    url="github.com/1Danish-00/compressorqueue",
                ),
                Button.url("Developer (Original)", url="t.me/danish_00"),
            ],
            [Button.url("Fork Maintainer", url="t.me/Col_serra")],
        ],
    )


async def temp_unauth(event, args, client):
    """
    Un-authorise a user or chat
    Requires either reply to message or user_id as args
    """
    sender = event.sender_id
    error = "Failed!,\nCan't remove from temporarily allowed users"
    if not user_is_owner(sender):
        return event.reply("Not Happening.")
    if event.is_reply:
        rep_event = await event.get_reply_message()
        new_id = rep_event.sender_id
    else:
        if args is not None:
            args = args.strip()
            if args.isdigit():
                new_id = int(args)
            else:
                return await event.reply(
                    f"What do you mean by  `{args}` ?\nneed help? send /unpermit"
                )
        else:
            return await event.reply(
                "Either reply to a message sent by the user you want to remove from temporarily allowed users or send /unpermit (user-id)\nExample:\n  /unpermit 123456"
            )
    if new_id == sender:
        return await event.reply("Why, oh why did you try to unpermit yourself?")
    if user_is_owner(new_id):
        return await event.reply(f"{error} because user is already a privileged user")
    if not user_is_allowed(new_id):
        return await event.reply(
            f"{error} because user is not in the temporary allowed user list"
        )
    try:
        new_user = await event.client.get_entity(new_id)
        new_user = new_user.first_name
    except Exception:
        new_user = new_id
    rm_temp_user(str(new_id))
    await save2db2()
    return await event.reply(
        f"Removed `{new_user}` from temporarily allowed users {enmoji()}"
    )


async def temp_auth(event, args, client):
    """
    Authorizes a chat or user,
    Requires either a reply to message or user_id as argument
    """
    sender = str(event.sender_id)
    error = "Failed!,\nCan't add to temporarily allowed users"
    if not user_is_owner(sender):
        return event.reply("Nope, not happening.")
    if event.is_reply:
        rep_event = await event.get_reply_message()
        new_id = rep_event.sender_id
    else:
        if args is not None:
            args = args.strip()
            if args.isdigit():
                new_id = args
            elif args.startswith("-100") and (args.lstrip("-100")).isdigit():
                new_id = args
            else:
                return await event.reply(
                    f"What do you mean by  `{args}` ?\nneed help? send /permit"
                )
        else:
            return await event.reply(
                "Either reply to a message sent by the user you want to add to temporarily allowed users or send /permit (user-id)\nExample:\n  /permit 123456"
            )
    new_id = str(new_id)
    if new_id == sender:
        return await event.reply("Why, oh why did you try to permit yourself?")
    if user_is_owner(new_id):
        return await event.reply(f"{error} because user is already a privileged user")
    if user_is_allowed(new_id):
        return await event.reply(f"{error} because user is already added")
    try:
        new_user = await event.client.get_entity(new_id)
        new_user = new_user.first_name
    except Exception:
        new_user = new_id
    add_temp_user(new_id)
    await save2db2()
    return await event.reply(
        f"Added `{new_user}` to temporarily allowed users {enmoji()}"
    )


async def icommands(event):
    await event.edit(
        """`
start - check if bot is awake and get usage.
restart -  restart bot
update - update bot
nuke - ☢️ nuke bot
bash - /bash + command
eval - evaluate code
pause - prevent bot from encoding
peval - same as eval but with pyrogram
ping - ping!
permit - add a temporary user
unpermit - removes a temporary user
l - add link to queue
queue - list queue
forward - manually forward a message to fchannel
v - turn v2,3,4… on (with message) or off
download - download a file or link to bot
upload - upload from a local directory or link
rename - rename a video file/link
mux - remux a file
get - get current ffmpeg code
set - set custom ffmpeg code
reset - reset default ffmpeg code
filter - filter & stuff
vfilter - view filter
groupenc - allow encoding in group toggle
delfilter - delete filter
name - quick filter with anime_title
vname - get list of name filter
delname - delete name filter
status - 🆕 get bot's status
showthumb - 🖼️ show current thumbnail
parse - toggle parsing with captions or anilist
groupenc - turn off/on encoding in groups
cancelall - ❌ clear cached downloads & queued files
clear - clear queued files
logs - get bot logs
help - same as start`

All above commands accept '-h' / '--help' arguments to
get more detailed help about each command.
        """,
        buttons=[Button.inline("🔙 Back", data="ihelp")],
    )
