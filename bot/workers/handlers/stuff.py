import os
import shutil
import time

import psutil

from bot import Button, botStartTime, dt, subprocess, version_file
from bot.config import conf
from bot.fun.emojis import enmoji
from bot.utils.bot_utils import add_temp_user, get_readable_file_size, rm_temp_user
from bot.utils.bot_utils import time_formatter as tf
from bot.utils.db_utils import save2db2
from bot.utils.msg_utils import (
    edit_message,
    pm_is_allowed,
    reply_message,
    temp_is_allowed,
    user_is_allowed,
    user_is_owner,
)
from bot.utils.os_utils import file_exists


async def up(event, args, client):
    """ping bot!"""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    ist = dt.now()
    msg = await reply_message(event, "…")
    st = dt.now()
    await edit_message(msg, "`Ping…`")
    ed = dt.now()
    ims = (st - ist).microseconds / 1000
    ms = (ed - st).microseconds / 1000
    await edit_message(msg, "**Pong!**\n`{}` __ms__, `{}` __ms__".format(ims, ms))


async def status(event, args, client):
    """Gets status of bot and server where bot is hosted.
    Requires no arguments."""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    last_commit = "UNAVAILABLE!"
    if os.path.exists(".git"):
        try:
            last_commit = subprocess.check_output(
                ["git log -1 --date=short --pretty=format:'%cd || %cr'"], shell=True
            ).decode()
        except Exception:
            pass

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
    msg2 = (
        f"{msg1}I've been alive for `{currentTime}` and i'm ready to encode videos 😗"
    )
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    user = event.sender_id
    if not user_is_owner(user) and event.is_private:
        if not pm_is_allowed(in_pm=True):
            return await event.delete()
    if temp_is_allowed(user):
        msg = msg3
    elif not user_is_allowed(user):
        priv = await event.client.get_entity(int(conf.OWNER.split()[0]))
        msg = f"{msg1}You're not allowed access to this bot"
        msg += f"\nAsk [{priv.first_name}](tg://user?id={conf.OWNER.split()[0]}) "
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
        "\n\nFor available commands click the Commands button below.",
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
    msg2 = (
        f"{msg1}I've been alive for `{currentTime}` and i'm ready to encode videos 😗"
    )
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    if temp_is_allowed(sender):
        msg = msg3
    elif not user_is_allowed(sender):
        priv = await event.client.get_entity(int(conf.OWNER.split()[0]))
        msg = f"{msg1}You're not allowed access to this bot"
        msg += f"\nAsk [{priv.first_name}](tg://user?id={conf.OWNER.split()[0]}) "
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
            if args.lstrip("-").isdigit():
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
    sender = event.sender_id
    error = "Failed!,\nCan't add to temporarily allowed users"
    if not user_is_owner(sender):
        return event.reply("Nope, not happening.")
    if event.is_reply:
        rep_event = await event.get_reply_message()
        new_id = rep_event.sender_id
    else:
        if args is not None:
            args = args.strip()
            if args.lstrip("-").isdigit():
                new_id = args
            else:
                return await event.reply(
                    f"What do you mean by  `{args}` ?\nneed help? send /permit"
                )
        else:
            return await event.reply(
                "Either reply to a message sent by the user you want to add to temporarily allowed users or send /permit (user-id)\nExample:\n  /permit 123456"
            )
    new_id = int(new_id)
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
    add_temp_user(str(new_id))
    await save2db2()
    return await event.reply(
        f"Added `{new_user}` to temporarily allowed users {enmoji()}"
    )


async def icommands(event):
    s = conf.CMD_SUFFIX or str()
    await event.edit(
        f"""`
start{s} - check if bot is awake and get usage.
restart{s} -  restart bot
update{s} - update bot
nuke{s} - ☢️ nuke bot
bash{s} - /bash + command
eval{s} - evaluate code
pause{s} - prevent bot from encoding
peval{s} - same as eval but with pyrogram
ping - ping!
permit{s} - add a temporary user
unpermit{s} - removes a temporary user
add{s} - add video to queue
l{s} - add link to queue
ql{s} - add torrent link to queue
s{s} - select files from torrent to encode
queue{s} - list queue
batch{s} - preview batches
list{s} - list all files in a torrent
forward{s} - manually forward a message to fchannel
v{s} - turn v2,3,4… on (with message) or off
download{s} - download a file or link to bot
upload{s} - upload from a local directory or link
rename{s} - rename a video file/link
mux{s} - remux a file
get{s} - get current ffmpeg code
set{s} - set custom ffmpeg code
reset{s} - reset default ffmpeg code
mset{s} - set, reset, disable mux_args
mget{s} - view current mux_args
filter{s} - filter & stuff
vfilter{s} - view filter
groupenc{s} - allow encoding in group toggle
delfilter{s} - delete filter
airing{s} - get anime airing info
anime{s} - get anime info
name{s} - quick filter with anime_title
vname{s} - get list of name filter
delname{s} - delete name filter
rss{s} - edit, delete & subscribe rss feeds
status{s} - 🆕 get bot's status
showthumb{s} - 🖼️ show current thumbnail
parse{s} - toggle parsing with captions or anilist
groupenc{s} - turn off/on encoding in groups
cancelall{s} - ❌ clear cached downloads & queued files
clear{s} - clear queued files
logs{s} - get bot logs
help{s} - same as start`

All above commands accept '-h' / '--help' arguments to get more detailed help about each command.
        """,
        buttons=[Button.inline("🔙 Back", data="ihelp")],
    )
