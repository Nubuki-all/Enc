import os
import shutil
from pathlib import Path

import psutil

from bot import asyncio, botStartTime, time
from bot.utils.ani_utils import qparse
from bot.utils.bot_utils import (
    decode,
    enc_canceller,
    get_queue,
    hbs,
    time_formatter,
    u_cancelled,
)
from bot.utils.log_utils import logger
from bot.utils.msg_utils import clean_old_message, user_is_owner
from bot.utils.os_utils import file_exists, s_remove


async def pres(e):
    try:
        _id = f"{e.chat_id}:{e.message_id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(e)
        process, dl, out, user_id = req_info
        _dir, ename = os.path.split(out)
        os.path.split(dl)[1]
        if _dir != "encode":
            ans = f"Muxing:\n{ename}"
            if file_exists("thumb3.jpg"):
                ans += "\n\nAnilist thumbnail:\nYes"
            return await e.answer(ans, alert=True)
        queue = get_queue()
        length = len(queue)
        ansa = f"Encoding:\n{ename}"
        if file_exists("thumb2.jpg"):
            ansa += "\n\nAnilist thumbnail:\nYes"
        if length > 1:
            # queue[list(queue.keys())[1]]
            file_name, _id, v = list(queue.values())[1]
            next_ = await qparse(file_name, v)
            next_ = (next_[:45] + "…") if len(next_) > 45 else next_
            ansa += f"\n\nNext up:\n{next_}\n\nRemains:- {length - 1}"
        await e.answer(ansa, cache_time=0, alert=True)
    except Exception:
        await logger(Exception)
        ansa = "YIKES"
        await e.answer(
            ansa,
        )


async def skip(e):
    _id = f"{e.chat_id}:{e.message_id}"
    req_info = decode(_id)
    if not req_info:
        return await clean_old_message(e)
    process, dl, en, user_id = req_info
    if not (user_is_owner(e.query.user_id) or user_id != e.query.user_id):
        ans = "You're not allowed to do this!"
        return await e.answer(ans)
    if not process:
        await e.answer("Cancelling…")
        await asyncio.sleep(2)
        await e.delete()
        return u_cancelled().append(_id)
    ans = "Cancelling encoding please wait…"
    await e.answer(ans)
    process.terminate()
    # await e.delete()
    s_remove(dl)
    s_remove(en)
    enc_canceller().update({_id: e.query.user_id})

    return


async def stats(e):
    try:
        _id = f"{e.chat_id}:{e.message_id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(e)
        process, dl, out, user_id = req_info
        ot = hbs(int(Path(out).stat().st_size))
        ov = hbs(int(Path(dl).stat().st_size))
        _dir, name = os.path.split(dl)
        input = (name[:45] + "…") if len(name) > 45 else name
        currentTime = time_formatter(time.time() - botStartTime)
        total, used, free = shutil.disk_usage(".")
        total = hbs(total)
        used = hbs(used)
        free = hbs(free)
        cpuUsage = psutil.cpu_percent(interval=0.5)
        ans = f"CPU: {cpuUsage}%\n\nTotal Disk Space:\n{total}\n\nDownloaded:\n{ov}\n\nFileName:\n{input}\n\nEncoded:\n{ot}\n\nBot Uptime:\n{currentTime}\n\nUsed: {used}  Free: {free}"
        await e.answer(ans, alert=True)
    except Exception:
        await logger(Exception)
        currentTime = time_formatter(time.time() - botStartTime)
        total, used, free = shutil.disk_usage(".")
        total = hbs(total)
        info = f"Error 506: An unknown error occurred.\n\nOther Info\n═══════════\nBot Uptime: {currentTime}\n\nTotal Disk Space: {total}"
        await e.answer(
            info,
            alert=True,
        )
