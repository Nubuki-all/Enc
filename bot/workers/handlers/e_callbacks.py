import os
import shutil
from pathlib import Path

import psutil
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from bot import asyncio, botStartTime, pyro, time
from bot.utils.ani_utils import qparse
from bot.utils.batch_utils import get_batch_list
from bot.utils.bot_utils import (
    decode,
    enc_canceller,
    get_queue,
    hbs,
    time_formatter,
    u_cancelled,
)
from bot.utils.log_utils import logger
from bot.utils.msg_utils import clean_old_message, turn, user_is_owner
from bot.utils.os_utils import file_exists, s_remove

#######! ENCODE CALLBACK HANDLERS !#######


async def get_next(length, queue):
    try:
        if length > 1:
            file_name, _id, v_f = list(queue.values())[1]
            v, f, m, n, au = v_f
            next_ = (
                await qparse(file_name, v, f, n, au[0])
                if m[1].lower() != "batch."
                else "[Batch]: " + file_name
            )
            next_ = (next_[:45] + "…") if len(next_) > 45 else next_
            if length > 2:
                file_name, _id, v_f = list(queue.values())[2]
                v, f, m, n, au = v_f
                next2_ = "\n" + (
                    await qparse(file_name, v, f, n, au[0])
                    if m[1].lower() != "batch."
                    else "[Batch]: " + file_name
                )
                next2_ = (next2_[:45] + "…") if len(next2_) > 45 else next2_
                next2_ = next2_ + f" (+{length - 3})" if length > 3 else next2_
            else:
                next2_ = str()
            return next_, next2_
    except Exception:
        log(Exception)
    return None, None


async def pres(e):
    try:
        _id = f"{e.chat_id}:{e.message_id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(e)
        process, dl, out, user_id, stime = req_info
        _dir, ename = os.path.split(out)
        os.path.split(dl)[1]
        if _dir != "encode":
            ans = f"Muxing:\n{ename}"
            return await e.answer(ans, alert=True)
        queue = get_queue()
        length = len(queue)
        ansa = str()
        if file_exists("thumb2.jpg"):
            ansa += "\n\nAnilist thumbnail:\nYes"
        file_name, _id, v_f = list(queue.values())[0]
        v, f, m, n, au = v_f
        if m[1].lower() == "batch.":
            _dir, name_ = os.path.split(dl)
            nxt_, left = await get_batch_list(
                exclude=name_, limit=2, v=v, f=f, get_nleft=True
            )
            if len(nxt_) == 0:
                next_, next2_ = await get_next(length, queue)
            elif len(nxt_) == 1:
                next_, next2_ = nxt_[0], str()
                length = 2
            else:
                next_, next2_ = nxt_
                next_ += "\n"
                next2_ += f" (+{left})" if left else str()
                length = left + 3 if left else 3
        else:
            next_, next2_ = await get_next(length, queue)
        if next_:
            ansa += f"\n\nNext up:\n{next_}{next2_}\n\nRemains:- {length - 1}"
        ansa = ansa or "Wow such emptiness 🐱."
        await e.answer(ansa, cache_time=0, alert=True)
    except Exception as e:
        await logger(Exception)
        ansa = "YIKES:\n" + str(e)
        await e.answer(
            ansa,
        )


async def skip(e):
    _id = f"{e.chat_id}:{e.message_id}"
    req_info = decode(_id)
    if not req_info:
        return await clean_old_message(e)
    process, dl, en, user_id, stime = req_info
    if not (user_is_owner(e.query.user_id) or user_id == e.query.user_id):
        ans = "You're not allowed to do this!"
        return await e.answer(ans)
    if not process:
        await e.answer("Cancelling…")
        await asyncio.sleep(2)
        await e.delete()
        return u_cancelled().append(_id)
    ans = "Cancelling encoding please wait…"
    await e.answer(ans)
    process.kill()
    # await e.delete()
    s_remove(dl)
    s_remove(en)
    enc_canceller().update({_id: e.query.user_id})

    return


async def stats(e):
    try:
        _id = f"{e.chat_id}:{e.message_id}"
        data = e.pattern_match.group(1).decode().strip()
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(e)
        process, dl, out, user_id, stime = req_info
        ot = hbs(int(Path(out).stat().st_size))
        ov = hbs(int(Path(dl).stat().st_size))
        _dir, name = os.path.split(dl)
        input = (name[:45] + "…") if len(name) > 45 else name
        currentTime = time_formatter(time.time() - botStartTime)
        total, used, free = shutil.disk_usage(".")
        total = hbs(total)
        used = hbs(used)
        free = hbs(free)
        elapsed = time_formatter(time.time() - stime)
        cpuUsage = psutil.cpu_percent(interval=0.5)
        if data == "0":
            ans = f"Downloaded:\n{ov}\n\nFileName:\n{input}\n\nEncoded:\n{ot}\n\nElapsed time:\n{elapsed}"
        elif data == "1":
            ans = f"CPU: {cpuUsage}%\n\nTotal Disk Space:\n{total}\n\nBot Uptime:\n{currentTime}\n\nUsed: {used}  Free: {free}"
        elif data == "2":
            ans = f"CPU: {cpuUsage}%\n\nTotal Disk Space:\n{total}\n\nDownloaded:\n{ov}\n\nEncoded:\n{ot}\n\nElapsed:\n{elapsed}\n\nBot Uptime:\n{currentTime}\n\nUsed: {used}  Free: {free}"
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


#######! DOWNLOAD CALLBACK HANDLERS !#######


async def dl_stat(client, query):
    try:
        query.data.split()
        msg = query.message
        if not msg:
            return await logger(e="Message too old!")
        if msg.empty:
            return await logger(e="An error occurred while fetching message details.")
        _id = f"{msg.chat.id}:{msg.id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(query, True)
        d = req_info[0]
        dl = d.path
        if file_exists(dl):
            dls = dl
        elif file_exists(dls := (dl + ".!qB")):
            pass
        else:
            dls = f"{dl}.temp"
        file_name = (os.path.split(d.file_name))[1]
        ov = hbs(int(Path(dls).stat().st_size))
        queue = get_queue()
        ver, fil, mode, n, au = (list(queue.values())[0])[2]
        q = await qparse(file_name, ver, fil, n, au[0])
        ans = f"➡️:\n{q}"
        ans += "\n\n"
        ans += f'{"Current " if not d.uri else str()}Size:\n{ov}'
        ans += "\n\n"
        ans += f"Elapsed time:\n" + time_formatter(time.time() - d.time)
        await query.answer(ans, cache_time=0, show_alert=True)
    except Exception:
        await logger(Exception)
        ans = "Yikes 😬"
        await query.answer(ans, cache_time=0, show_alert=True)


async def download_button_callback(client, callback_query):
    try:
        msg = callback_query.message
        if not msg:
            return await logger(e="Message too old!")
        if msg.empty:
            return await logger(e="An error occurred while fetching message details.")
        _id = f"{msg.chat.id}:{msg.id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(callback_query, True)
        d = req_info[0]
        if not (
            user_is_owner(callback_query.from_user.id)
            or callback_query.from_user.id == d.sender
        ):
            return await callback_query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        d.is_cancelled = True
        d.canceller = await pyro.get_users(callback_query.from_user.id)
        await callback_query.answer(
            "Cancelling download please wait…", show_alert=False
        )
    except Exception:
        await logger(Exception)


async def v_info(client, query):
    try:
        msg = query.message
        if not msg:
            return await logger(e="Message too old!")
        if msg.empty:
            return await logger(e="An error occurred while fetching message details.")
        _id = f"{msg.chat.id}:{msg.id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(query, True)
        d = req_info[0]
        if not (user_is_owner(query.from_user.id) or query.from_user.id == d.sender):
            return await query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        await query.answer("Please wait…")
        d.display_dl_info = True
    except Exception:
        await logger(Exception)


async def back(client, query):
    try:
        msg = query.message
        if not msg:
            return await logger(e="Message too old!")
        if msg.empty:
            return await logger(e="An error occurred while fetching message details.")
        _id = f"{msg.chat.id}:{msg.id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(query, True)
        d = req_info[0]
        if not (user_is_owner(query.from_user.id) or query.from_user.id == d.sender):
            return await query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        await query.answer("Please wait…")
        d.display_dl_info = False
    except Exception:
        await logger(Exception)


#######! UPLOAD CALLBACK HANDLERS !#######


async def upload_button_callback(client, callback_query):
    try:
        msg = callback_query.message
        if not msg:
            return await logger(e="Message too old!")
        if msg.empty:
            return await logger(e="An error occurred while fetching message details.")
        _id = f"{msg.chat.id}:{msg.id}"
        req_info = decode(_id)
        if not req_info:
            return await clean_old_message(callback_query, True)
        d = req_info[0]
        if not (
            user_is_owner(callback_query.from_user.id)
            or callback_query.from_user.id == d.sender
        ):
            return await callback_query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        d.is_cancelled = True
        d.canceller = callback_query.from_user.id
        await callback_query.answer("Cancelling upload please wait…", show_alert=False)
    except Exception:
        await logger(Exception)


#######! TURN CALLBACK HANDLERS !#######


async def cancel_turn_callback(client, query):
    try:
        turn_id = query.data.split()[1]
        if not turn(turn_id):
            return await clean_old_message(query, True)
        if not user_is_owner(query.from_user.id):
            return await query.answer("You're not allowed to do this!")
        await query.answer("Cancelling…")
        turn().remove(turn_id)
        await query.message.delete()
    except Exception as e:
        await logger(Exception)
        await query.answer(f"Error: {e}", show_alert=True)


pyro.add_handler(
    CallbackQueryHandler(download_button_callback, filters=regex("^cancel_download"))
)
pyro.add_handler(CallbackQueryHandler(v_info, filters=regex("^dl_info")))
pyro.add_handler(CallbackQueryHandler(back, filters=regex("^back")))
pyro.add_handler(CallbackQueryHandler(dl_stat, filters=regex("^more")))


pyro.add_handler(
    CallbackQueryHandler(upload_button_callback, filters=regex("^cancel_upload"))
)


pyro.add_handler(
    CallbackQueryHandler(cancel_turn_callback, filters=regex("^cancel_turn"))
)
