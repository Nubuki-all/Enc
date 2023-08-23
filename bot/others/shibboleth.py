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

import shutil
import signal
import time
from pathlib import Path

import psutil

from .util import *
from .worker import *


async def upload2(from_user_id, filepath, reply, thum, caption, message=""):
    async with bot.action(from_user_id, "file"):
        await reply.edit("🔺Uploading🔺")
        u_start = time.time()
        if UNLOCK_UNSTABLE and message:
            s = await message.reply_document(
                document=filepath,
                quote=True,
                thumb=thum,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=(app, "Uploading 👘", reply, u_start),
            )
        else:
            s = await app.send_document(
                document=filepath,
                chat_id=from_user_id,
                force_document=True,
                thumb=thum,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=(app, "Uploading 👘", reply, u_start),
            )
    return s


async def cancel_dl(e):
    if (
        str(e.query.user_id) not in OWNER
        and e.query.user_id != DEV
        and str(e.query.user_id) not in str(USER_MAN[0])
    ):
        ans = "You're not allowed to do this!"
        return await e.answer(ans, cache_time=0, alert=False)
    try:
        ans = "Cancelling downloading please wait…"
        await e.answer(ans, cache_time=0, alert=False)
        global download_task
        DOWNLOAD_CANCEL.append(e.query.user_id)
        try:
            download_task.cancel()
        except Exception:
            pass
        for proc in psutil.process_iter():
            processName = proc.name()
            processID = proc.pid
            print(processName, " - ", processID)
            if processName == "aria2c":
                os.kill(processID, signal.SIGKILL)
        await qclean()
        ans = "Download cancelled. Reporting…"
        await e.answer(ans, cache_time=0, alert=False)
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def pres(e):
    try:
        wah = e.pattern_match.group(1).decode("UTF-8")
        wh = decode(wah)
        out, dl, id = wh.split(";")
        nme = out.split("/")[1]
        name = dl.split("/")[1]
        thumb = Path("thumb2.jpg")
        if thumb.is_file():
            oho = "Yes"
        else:
            oho = "No"
        por = str(QUEUE)
        t = len(QUEUE)
        if t > 0:
            if name in por and t < 2:
                q = "N/A"
                t = t - 1
            elif name in por:
                q, file = QUEUE[list(QUEUE.keys())[1]]
                q = await qparse(q)
                t = t - 1
            else:
                q, file = QUEUE[list(QUEUE.keys())[0]]
                q = await qparse(q)
        else:
            q = "N/A"
        q = (q[:45] + "…") if len(q) > 45 else q
        ansa = f"Auto-generated Filename:\n{nme}\n\nAuto-Generated Thumbnail:\n{oho}\n\nNext Up:\n{q}\n\nQueue Count:\n{t}"
        await e.answer(ansa, cache_time=0, alert=True)
    except AttributeError:
        ansa = "Oops! data of this button was lost,\n most probably due to restart.\nAnd as such the outdated message will be removed…"
        await e.answer(ansa, cache_time=0, alert=False)
        await asyncio.sleep(5)
        try:
            rep_e = await (await e.get_message()).get_reply_message()
            await rep_e.delete()
        except Exception:
            ers = traceback.format_exc()
            LOGS.info("[DEBUG] -pres- " + ers)
        await e.delete()
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
        ansa = "YIKES"
        await e.answer(
            ansa,
            cache_time=0,
            alert=True,
        )


async def dl_stat(e):
    try:
        wah = e.pattern_match.group(1).decode("UTF-8")
        dl = decode(wah)
        if not dl:
            raise AttributeError("No data")
        dl_check = Path(dl)
        if dl_check.is_file():
            dls = dl
        else:
            dls = f"{dl}.temp"
        ov = hbs(int(Path(dls).stat().st_size))
        name = dl.split("/")[1]
        input = (name[:45] + "…") if len(name) > 45 else name
        q = await qparse(name)
        ans = f"📥 Downloading:\n{input}\n\n⭕ Current Size:\n{ov}\n\n\n{enmoji()}:\n{q}"
        await e.answer(ans, cache_time=0, alert=True)
    except AttributeError:
        ansa = "Oops! data of this button was lost,\n most probably due to restart.\nAnd as such the outdated message will be removed…"
        await e.answer(ansa, cache_time=0, alert=False)
        await asyncio.sleep(5)
        try:
            rep_e = await (await e.get_message()).get_reply_message()
            await rep_e.delete()
        except Exception:
            ers = traceback.format_exc()
            LOGS.info("[DEBUG] -dl_stat- " + ers)
        await e.delete()
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
        ans = "Yikes 😬"
        await e.answer(ans, cache_time=0, alert=True)


async def stats(e):
    try:
        wah = e.pattern_match.group(1).decode("UTF-8")
        wh = decode(wah)
        out, dl, id = wh.split(";")
        ot = hbs(int(Path(out).stat().st_size))
        ov = hbs(int(Path(dl).stat().st_size))
        dt.now()
        name = dl.split("/")[1]
        input = (name[:45] + "…") if len(name) > 45 else name
        currentTime = get_readable_time(time.time() - botStartTime)
        total, used, free = shutil.disk_usage(".")
        total = get_readable_file_size(total)
        used = get_readable_file_size(used)
        free = get_readable_file_size(free)
        get_readable_file_size(psutil.net_io_counters().bytes_sent)
        get_readable_file_size(psutil.net_io_counters().bytes_recv)
        cpuUsage = psutil.cpu_percent(interval=0.5)
        psutil.virtual_memory().percent
        psutil.disk_usage("/").percent
        ans = f"CPU: {cpuUsage}%\n\nTotal Disk Space:\n{total}\n\nDownloaded:\n{ov}\n\nFileName:\n{input}\n\nCompressing:\n{ot}\n\nBot Uptime:\n{currentTime}\n\nUsed: {used}  Free: {free}"
        await e.answer(ans, cache_time=0, alert=True)
    except AttributeError:
        ansa = "Oops! data of this button was lost,\n most probably due to restart.\nAnd as such the outdated message will be removed…"
        await e.answer(ansa, cache_time=0, alert=False)
        await asyncio.sleep(5)
        try:
            rep_e = await (await e.get_message()).get_reply_message()
            await rep_e.delete()
        except Exception:
            ers = traceback.format_exc()
            LOGS.info("[DEBUG] -stats- " + ers)
        await e.delete()
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
        currentTime = get_readable_time(time.time() - botStartTime)
        total, used, free = shutil.disk_usage(".")
        total = get_readable_file_size(total)
        info = f"Error 404: File | Info not Found 🤔\nMaybe Bot was restarted\nKindly Resend Media\n\nOther Info\n═══════════\nBot Uptime: {currentTime}\n\nTotal Disk Space: {total}"
        await e.answer(
            info,
            cache_time=0,
            alert=True,
        )


async def encod(event):
    try:
        EVENT2.clear()
        EVENT2.append(event)
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
