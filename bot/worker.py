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

from .funcn import *
from .util import (
    custcap,
    dynamicthumb,
    get_readable_file_size,
    get_readable_time,
    parse,
    parse_dl,
)
from .worker import *


async def getlogs(event):
    if str(event.sender_id) not in OWNER and event.sender_id != DEV:
        return await event.delete()
    await event.client.send_file(event.chat_id, file=LOG_FILE_NAME, force_document=True)


async def save2db():
    if DATABASE_URL:
        y = json.dumps(QUEUE)
        queue.delete_many({})
        queue.insert_one({"queue": y})


async def save2db2(mara, para):
    if DATABASE_URL:
        y = json.dumps(para)
        mara.delete_many({})
        mara.insert_one({"queue": [y, "0"]})


async def on_termination():
    try:
        for i in OWNER.split():
            await bot.send_message(int(i), f"**I'm {enquip2()} {enmoji2()}**")
    except Exception:
        pass
    try:
        if LOG_CHANNEL:
            me = await app.get_users("me")
            await bot.send_message(
                int(LOG_CHANNEL), f"**{me.first_name} is {enquip2()} {enmoji2()}**"
            )
    except BaseException:
        pass
    try:
        if FCHANNEL_STAT:
            estat = "**#Dead**"
            await stateditor(estat, int(FCHANNEL), int(FCHANNEL_STAT))
    except Exception:
        pass
    # More cleanup code?
    exit()


async def version2(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    temp = ""
    try:
        temp = event.text.split(" ", maxsplit=1)[1]
    except Exception:
        pass
    if temp:
        VERSION2.clear()
        VERSION2.append(temp)
        await event.reply(f"**Added V2 Tag Successfully!\nV2 Reason:** `{temp}`")
    else:
        VERSION2.clear()
        await event.reply("**Removed V2 Tag Successfully!**")


async def discap(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    temp = ""
    try:
        temp = event.text.split(" ", maxsplit=1)[1]
    except Exception:
        pass
    if temp.casefold() == "caption":
        ttx = Path("cap.txt")
        if ttx.is_file():
            os.remove(ttx)
            await event.reply("**Successfully Enabled Parse By Caption**")
        else:
            file = open(ttx, "w")
            file.close()
            await event.reply("**Successfully Disabled Parse By Caption**")
    else:
        ttx = Path("parse.txt")
        if ttx.is_file():
            os.remove(ttx)
            await event.reply(
                "**Successfully Enabled Anilist parsing & Auto-thumbnail**"
            )
        else:
            file = open(ttx, "w")
            file.close()
            await event.reply(
                "**Successfully Disabled Anilist Parsing & Auto-thumbnail**"
            )


async def clean(event):
    if str(event.sender_id) not in OWNER and event.sender_id != DEV:
        return await event.delete()
    await event.reply("**Cleared Queued, Working Files and Cached Downloads!**")
    WORKING.clear()
    QUEUE.clear()
    if DATABASE_URL:
        queue.delete_many({})
    os.system("rm -rf downloads/*")
    os.system("rm -rf encode/*")
    for proc in psutil.process_iter():
        processName = proc.name()
        processID = proc.pid
        print(processName, " - ", processID)
        if processName == "ffmpeg":
            os.kill(processID, signal.SIGKILL)
    return


async def download2(dl, file, message, e):
    try:
        global download_task
        if message:
            ttt = time.time()
            media_type = str(message.media)
            if media_type == "MessageMediaType.DOCUMENT":
                media_mssg = "`Downloading a queued file…`\n"
            else:
                media_mssg = "`Downloading a queued video…`\n"
            download_task = asyncio.create_task(
                app.download_media(
                    message=message,
                    file_name=dl,
                    progress=progress_for_pyrogram,
                    progress_args=(app, media_mssg, e, ttt),
                )
            )
        else:
            download_task = asyncio.create_task(
                app.download_media(
                    message=file,
                    file_name=dl,
                )
            )
        return download_task
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


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
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def update2(client, message):
    try:
        if str(message.from_user.id) in OWNER:
            upt_mess = "Updating…"
            reply = await message.reply(f"`{upt_mess}`")
            await enquoter(upt_mess, reply)
            await updater()
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def nuke(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        rst = await event.reply("`Trying To Nuke ☣️`")
        await asyncio.sleep(1)
        await rst.edit("`☢️ Nuking Please Wait…`")
        os.system("kill -9 -1")
    except Exception:
        await event.reply("Error Occurred")
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def restart(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        rst = await event.reply("`Trying To Restart`")
        await asyncio.sleep(1)
        rst_msg = "Restarting Please Wait…"
        rst = await rst.edit(f"`{rst_msg}`")
        await enquoter(rst_msg, rst)
        await qclean()
        os.execl(sys.executable, sys.executable, "-m", "bot")
    except Exception:
        await event.reply("Error Occurred")
        ers = traceback.format_exc()
        LOGS.info(ers)


async def listqueue(event):
    if str(event.sender_id) not in OWNER and str(event.sender_id) not in TEMP_USERS:
        return await event.delete()
    if not QUEUE:
        yo = await event.reply("Nothing In Queue")
        await asyncio.sleep(3)
        await yo.delete()
        return await event.delete()
    try:
        if WORKING:
            i = 0
        else:
            i = 1
        x = ""
        while i < len(QUEUE):
            y, yy = QUEUE[list(QUEUE.keys())[i]]
            ss = await app.get_users(yy)
            x += f"{i}. {y} ({ss.first_name})\n"
            i = i + 1
        if x:
            x += "\n**To remove an item from queue use** /clear <queue number>"
        else:
            x += "**Nothing Here** 🐱"
    except Exception:
        x = "No Pending Item in Queue 😒"
    yo = await event.reply(x)
    await asyncio.sleep(10)
    await event.delete()
    await yo.delete()


async def listqueuep(event):
    async with bot.action(event.sender_id, "typing"):
        if str(event.sender_id) not in OWNER and str(event.sender_id) not in TEMP_USERS:
            return await event.delete()
        if not QUEUE:
            yo = await event.reply("Nothing In Queue")
            await asyncio.sleep(3)
            await yo.delete()
            return await event.delete()
        try:
            if WORKING:
                i = 0
            else:
                i = 1
            x = ""
            while i < len(QUEUE):
                y, yy = QUEUE[list(QUEUE.keys())[i]]
                y = await qparse(y)
                x += f"{i}. {y}\n"
                i = i + 1
            if x:
                x += "\n**Queue based on auto-generated filename if you you want the actual queue use the command** /queue "
            else:
                x += "wow, such emptiness 😶"
        except Exception:
            x = "No Pending Item in Queue 😒"
        yo = await event.reply(x)
        await asyncio.sleep(10)
        await event.delete()
        await yo.delete()


async def encodestat():
    if FCHANNEL and FCHANNEL_STAT:
        if not QUEUE and not WORKING:
            x = "**Currently Resting…😑**"
            return x
        if not QUEUE:
            x = "**◉ Busy…**"
            return x
        try:
            if WORKING:
                i = 0
                x = "    **CURRENT ITEMS ON QUEUE:**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            else:
                i = 1
                y, yy = QUEUE[list(QUEUE.keys())[0]]
                y = await qparse(y)
                x = f"🟢. `{y}`\n\n    **CURRRENT ITEMS ON QUEUE:**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            while i < len(QUEUE):
                y, yy = QUEUE[list(QUEUE.keys())[i]]
                y = await qparse(y)
                x += f"{i}. `{y}`\n"
                i = i + 1
                if i > 5:
                    xr = len(QUEUE) - i
                    x += f"__+{xr} more…__\n"
                    break
            if len(QUEUE) == 1 and not WORKING:
                loc = await enquotes()
                x += f"Nothing Here; While you wait:\n\n{loc}"
        except Exception:
            y, yy = QUEUE[list(QUEUE.keys())[0]]
            y = await qparse(y)
            x = f"**Currently Encoding:** `{y}`\n\n**QUEUE:**\n──────\n`Nothing Here.`"
        me = await app.get_users("me")
        x += f"\n\nYours truly,\n  {enmoji()} `{me.first_name}`"
        return x


async def stateditor(x, channel, id):
    try:
        if channel and id:
            return await app.edit_message_text(channel, id, x)

    except Exception:
        pass


async def autostat():
    try:
        if FCHANNEL and FCHANNEL_STAT:
            CHECK = []
            while FCHANNEL_STAT:
                if not QUEUE and not WORKING:
                    if not CHECK:
                        CHECK.append(1)
                    else:
                        await asyncio.sleep(60)
                        continue
                else:
                    if CHECK:
                        CHECK.clear()
                if STARTUP:
                    estat = await encodestat()
                else:
                    estat = "**What's Popping 🪩**"
                await stateditor(estat, int(FCHANNEL), int(FCHANNEL_STAT))
                await asyncio.sleep(60)
    except Exception:
        pass


async def statuschecker():
    if not STARTUP:
        try:
            asyncio.create_task(autostat())
            loop = asyncio.get_running_loop()
            for signame in {"SIGINT", "SIGTERM", "SIGABRT"}:
                loop.add_signal_handler(
                    getattr(signal, signame),
                    lambda: asyncio.create_task(on_termination()),
                )
            # some other stuff to do ONLY on startup couldn't find a better way
            # even after more than 8 trials which i committed
            await asyncio.sleep(30)
        except Exception:
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
        STARTUP.append(1)


async def reffmpeg(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        os.system(f"rm -rf ffmpeg.txt")
        file = open("ffmpeg.txt", "w")
        file.write(str(FFMPEG) + "\n")
        file.close()
        await save2db2(ffmpegdb, FFMPEG)
        await event.reply(f"**Changed FFMPEG Code to**\n\n`{FFMPEG}`")
    except Exception:
        await event.reply("Error Occurred")
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def change(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        temp = ""
        try:
            temp = event.text.split(" ", maxsplit=1)[1]
        except Exception:
            pass
        if not temp:
            await event.reply(
                f"Setting ffmpeg failed\n**Try:**\n/set `(raw ffmpeg code Without brackets using the format specified in repo)`"
            )
            return
        os.system(f"rm -rf ffmpeg.txt")
        file = open("ffmpeg.txt", "w")
        file.write(str(temp) + "\n")
        file.close()
        await save2db2(ffmpegdb, temp)
        await event.reply(f"**Changed FFMPEG Code to**\n\n`{temp}`")
    except Exception:
        await event.reply("Error Occurred")
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def check(event):
    if str(event.sender_id) not in OWNER and event.sender_id != DEV:
        return await event.delete()
    with open("ffmpeg.txt", "r") as file:
        ffmpeg = file.read().rstrip()
        file.close()
    await event.reply(f"**Current FFMPEG Code Is**\n\n`{ffmpeg}`")


async def allowgroupenc(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    if GROUPENC:
        GROUPENC.clear()
        yo = await event.reply("**Turned off Successfully**")
        await asyncio.sleep(10)
        await yo.delete()
        await event.delete()
    else:
        GROUPENC.append(1)
        yo = await event.reply(
            "**Group Encoding Turned on Successfully**\n__Persists till bot reboots!__"
        )
        await asyncio.sleep(10)
        await yo.delete()
        await event.delete()


async def getthumb(event):
    if str(event.sender_id) not in OWNER and event.sender_id not in TEMP_USERS:
        return await event.delete()
    tbcheck = Path("thumb2.jpg")
    if tbcheck.is_file():
        thum = "thumb2.jpg"
    else:
        thum = "thumb.jpg"
    await event.client.send_file(
        event.chat_id,
        file=thum,
        force_document=False,
        caption="**Your Current Thumbnail.**",
    )


async def rmfilter(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        fl = "filter.txt"
        os.remove(fl)
        if DATABASE_URL:
            filterz.delete_many({})
        await event.reply("`Filters Deleted!`")
    except Exception:
        await event.reply("❌ No Filters Found To Delete")


async def vfilter(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        olif = Path("filter.txt")
        if olif.is_file():
            with open("filter.txt", "r") as file:
                fil = file.read()
                fil1 = fil.split("\n")[0]
                fil2 = fil.split("\n")[1]
                fil3 = fil.split("\n")[2]
                file.close()
            await event.reply(
                f"Bot Will Automatically:\n\n **Remove:-** `{fil1}`\n **Tag Files as:-** `{fil2}`\n **Tag Type as:-** `{fil3}`"
            )
        else:
            await event.reply("`❌ No Filters Found!`")
    except Exception:
        await event.reply(
            "An Error Occurred\n Filter was wrongly set check accepted  format with /filter"
        )


async def lock(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        temp = ""
        try:
            temp = event.text.split(" ", maxsplit=1)[1]
        except Exception:
            pass
        if not temp:
            await event.reply(
                f"`Locking Failed: send amount of time to lock in seconds`\nFor instance /lock 30\n\n**Peace**"
            )
            return
        if temp.casefold() == "disable" or temp.casefold() == "off":
            try:
                LOCKFILE.clear()
                return await event.reply("**Locking Cancelled**")
            except Exception:
                return await event.reply("**Unlocking Failed / Bot was not Locked**")
        try:
            int(temp)
        except Exception:
            return await event.reply(
                "**Locking failed: Send a number instead**\n For instance:\n /lock 900 to lock for 900 seconds or /lock 0 to lock infinitely till you cancel with /lock off"
            )
        if not LOCKFILE:
            ot = ""
            LOCKFILE.append(temp)
            await event.reply(f"**Locking for** `{temp}s`")
            lock_dur = f"for `{LOCKFILE[0]}s`"
            if int(LOCKFILE[0]) == 0:
                lock_dur = "Indefinitely!"
            try:
                for i in OWNER.split():
                    oo = await bot.send_message(
                        int(i), f"Bot has been locked {lock_dur}"
                    )
            except Exception:
                pass
            try:
                for i in TEMP_USERS.split():
                    ot = await bot.send_message(
                        int(i), f"Bot has been locked {lock_dur}"
                    )
            except Exception:
                pass
            if LOG_CHANNEL:
                log = int(LOG_CHANNEL)
                op = await bot.send_message(
                    log,
                    f"[{event.sender.first_name}](tg://user?id={event.sender_id}) locked the bot {lock_dur}",
                )
            countdown = int(LOCKFILE[0])
            while countdown > 1:
                await asyncio.sleep(1)
                countdown = countdown - 1
                if not LOCKFILE:
                    countdown = 1
            while countdown == 0:
                await asyncio.sleep(5)
                if not LOCKFILE:
                    countdown = 1
            LOCKFILE.clear()

            async def edito(rst):
                await rst.edit(
                    "**Lock Ended or cancelled and bot has been unlocked automatically**"
                )

            await edito(oo)
            if ot:
                await edito(ot)
            if LOG_CHANNEL:
                await edito(op)
            return
        if LOCKFILE:
            return await event.reply("**Bot already locked\nDo /lock off to unlock**")
    except Exception:
        await event.reply("Error Occurred")
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def filter(event):
    if str(event.sender_id) not in OWNER:
        return await event.delete()
    try:
        temp = ""
        try:
            temp = event.text.split(" ", maxsplit=1)[1]
        except Exception:
            pass
        if not temp:
            await event.reply(
                f"Setting filter failed\n**Try:**\n/filter `(whattoremove)`\n`(filetag)`\n`(typetag)`"
            )
            return
        os.system(f"rm -rf filter.txt")
        file = open("filter.txt", "w")
        file.write(str(temp))
        file.close()
        await save2db2(filterz, temp)
        await event.reply(f"**Changed filters to**\n\n`{temp}`")
    except Exception:
        await event.reply("Error Occurred")
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)


async def clearqueue(event):
    async with bot.action(event.sender_id, "typing"):
        if str(event.sender_id) not in OWNER and str(event.sender_id) not in TEMP_USERS:
            return await event.delete()
        temp = ""
        try:
            temp = event.text.split(" ", maxsplit=1)[1]
        except Exception:
            pass
        if temp:
            try:
                temp = int(temp)
                try:
                    q, user = QUEUE[list(QUEUE.keys())[temp]]
                    if str(event.sender_id) not in OWNER and event.sender_id != user:
                        return await event.reply(
                            "You didn't add this to queue so you can't remove it!"
                        )
                    QUEUE.pop(list(QUEUE.keys())[temp])
                    yo = await event.reply(f"{q} has been removed from queue")
                    await save2db()
                except Exception:
                    yo = await event.reply("Enter a valid queue number")
            except Exception:
                yo = await event.reply(
                    "Pass a number for an item on queue to be removed"
                )
        else:
            try:
                xx = "**Cleared the following files from queue:**\n"
                x = ""
                xxn = 1
                if WORKING:
                    i = 0
                else:
                    i = 1
                while i < len(QUEUE):
                    y, user = QUEUE[list(QUEUE.keys())[i]]
                    if (
                        str(event.sender_id) not in OWNER
                        and str(event.sender_id) not in TEMP_USERS
                    ):
                        i = i + 1
                    else:
                        QUEUE.pop(list(QUEUE.keys())[i])
                        x += f"{xxn}. {y} \n"
                    xxn = xxn + 1
            except Exception:
                ers = traceback.format_exc()
                xx = "⚠️"
                x = " __An Error occurred check /logs for more info__"
                LOGS.info(ers)
            if x:
                x = f"{xx}{x}"
            else:
                x = "**Nothing to clear!**"
            yo = await event.reply(x)
            if DATABASE_URL:
                await save2db()
        await asyncio.sleep(7)
        await event.delete()
        await yo.delete()
        return


async def thumb(event):
    if str(event.sender_id) not in OWNER and event.sender_id != DEV:
        return
    if not event.photo:
        return
    os.system("rm thumb.jpg")
    await event.client.download_media(event.media, file="thumb.jpg")
    await event.reply("**Thumbnail Saved Successfully.**")


async def qparse(q):
    kk = q
    if "[" in kk and "]" in kk:
        pp = kk.split("[")[0]
        qq = kk.split("]")[1]
        kk = pp + qq
    else:
        kk = kk
    aa = kk.split(".")[-1]
    namo = q
    if "v2" in namo:
        name = namo.replace("v2", "")
    else:
        name = namo
    bb2 = await parse(name, kk, aa)
    bb = bb2[0]
    return bb


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


async def enshell(cmd):
    # Create a subprocess and wait for it to finish
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    # Return the output of the command and the process object
    return (process, stdout.decode(), stderr.decode())


async def encod(event):
    try:
        EVENT2.clear()
        EVENT2.append(event)
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)


async def enleech(event):
    if str(event.sender_id) not in OWNER and event.sender_id != DEV:
        return
    try:
        temp = ""
        if event.is_reply:
            rep_event = await event.get_reply_message()
            try:
                temp = event.text.split(" ", maxsplit=1)[1]
            except Exception:
                pass
            if temp:
                if temp.isdigit():
                    temp = int(temp)
                    temp2 = rep_event.id
                    while temp > 0:
                        event2 = await bot.get_messages(event.chat_id, ids=temp2)
                        if event2 is None:
                            if LOCKFILE:
                                if LOCKFILE[0] == "leechlock":
                                    LOCKFILE.clear()
                            return await event.reply(
                                f"Resend uri links and try replying the first with /l again"
                            )
                        uri = event2.text
                        if is_url(uri) is True and uri.endswith("torrent"):
                            pass
                        else:
                            if LOCKFILE:
                                if LOCKFILE[0] == "leechlock":
                                    LOCKFILE.clear()
                            return await event2.reply("`Invalid torrent link`")
                        file_name = await get_leech_name(uri)
                        if file_name is None:
                            await event2.reply(
                                "`An error occurred probably an issue with aria2.`"
                            )
                            temp = temp - 1
                            temp2 = temp2 + 1
                            await asyncio.sleep(10)
                            continue
                        if not file_name:
                            await event2.reply(
                                "`Torrent is…\neither not a video\nor is a batch torrent which is currently not supported.`"
                            )
                            temp = temp - 1
                            temp2 = temp2 + 1
                            await asyncio.sleep(5)
                            continue
                        already_in_queue = False
                        for item in QUEUE.values():
                            if file_name in item:
                                await event2.reply(
                                    "**THIS TORRENT HAS ALREADY BEEN ADDED TO QUEUE**"
                                )
                                temp = temp - 1
                                temp2 = temp2 + 1
                                await asyncio.sleep(5)
                                already_in_queue = True
                                break
                        if already_in_queue:
                            continue
                        if not LOCKFILE:
                            LOCKFILE.append("leechlock")
                        if UNLOCK_UNSTABLE:
                            QUEUE.update({event2.id: [file_name, event.sender_id]})
                        else:
                            QUEUE.update({uri: [file_name, event.sender_id]})
                        await save2db()
                        await event2.reply(
                            "**Torrent added To Queue ⏰,** \n`Please Wait , Encode will start soon`"
                        )
                        temp = temp - 1
                        temp2 = temp2 + 1
                        await asyncio.sleep(5)
                    if LOCKFILE:
                        if LOCKFILE[0] == "leechlock":
                            LOCKFILE.clear()
                    return
                else:
                    return await event.reply(
                        f"**Pardon me, but what does*** `'{temp2}'` **mean?\noh and btw whatever you ran has failed."
                    )
            else:
                uri = rep_event.text
                if is_url(uri) is True and uri.endswith(".torrent"):
                    event_id = rep_event.id
                else:
                    return await rep_event.reply("`Invalid torrent link`")
        else:
            try:
                temp = event.text.split(" ", maxsplit=1)[1]
                uri = temp
            except Exception:
                pass
            if temp:
                if is_url(uri) is True and uri.endswith(".torrent"):
                    event_id = event.id
                else:
                    return await event.reply("`Invalid torrent link`")
            else:
                return await event.reply(
                    "`uhm you need to reply to or send command alongside a uri (torrent) link`"
                )
        file_name = await get_leech_name(uri)
        if file_name is None:
            return await event.reply(
                "`An error occurred probably an issue with aria2.`"
            )
        if not file_name:
            return await event.reply(
                "`Torrent is…\neither not a video\nor is a batch torrent which is currently not supported.`"
            )
        for item in QUEUE.values():
            if file_name in item:
                return await event.reply(
                    "**THIS TORRENT HAS ALREADY BEEN ADDED TO QUEUE**"
                )
        if UNLOCK_UNSTABLE:
            QUEUE.update({event_id: [file_name, event.sender_id]})
        else:
            QUEUE.update({uri: [file_name, event.sender_id]})
        await save2db()
        return await event.reply(
            "**Torrent added To Queue ⏰,** \n`Please Wait , Encode will start soon`"
        )
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
        if LOCKFILE:
            if LOCKFILE[0] == "leechlock":
                LOCKFILE.clear()
        return await event.reply("An Unknown error Occurred.")


async def pencode(message):
    try:
        inputer = str(message.chat.id)
        if inputer not in OWNER and inputer not in TEMP_USERS:
            try:
                act_inputer = str(message.from_user.id)
                if act_inputer not in OWNER and act_inputer not in TEMP_USERS:
                    return await message.delete()
                else:
                    if GROUPENC:
                        pass
                    else:
                        yo = await message.reply(
                            "#Warning\n\n**Pm me with files to encode instead\nOR\nclick /groupenc to turn on group encoding!**"
                        )
                        await asyncio.sleep(5)
                        await yo.delete()
                        return
            except BaseException:
                yo = await message.reply(f"{enmoji()}")
                await asyncio.sleep(5)
                return await yo.delete()
        if message.document:
            if message.document.mime_type not in video_mimetype:
                return
        event = await bot.get_messages(message.chat.id, ids=message.id)
        if WORKING or QUEUE or LOCKFILE:
            xxx = await message.reply("`Adding To Queue`", quote=True)
            media_type = str(message.media)
            if media_type == "MessageMediaType.VIDEO":
                doc = message.video
            else:
                doc = message.document
            sem = message.caption
            ttt = Path("cap.txt")
            if sem and "\n" in sem:
                sem = ""
            if sem and not ttt.is_file():
                name = sem
            else:
                name = doc.file_name
            if not name:
                name = "video_" + dt.now().isoformat("_", "seconds") + ".mp4"
            root, ext = os.path.splitext(name)
            if not ext:
                ext = ".mkv"
                name = root + ext
            for item in QUEUE.values():
                if name in item:
                    return await xxx.edit(
                        "**THIS FILE HAS ALREADY BEEN ADDED TO QUEUE**"
                    )
            if UNLOCK_UNSTABLE:
                user = message.chat.id
                QUEUE.update({message.id: [name, user]})
            else:
                user = message.from_user.id
                QUEUE.update({doc.file_id: [name, user]})
            await save2db()
            return await xxx.edit(
                "**Added To Queue ⏰,** \n`Please Wait , Encode will start soon`"
            )
        WORKING.append(1)
        xxx = await message.reply(
            "`Download Pending…` \n**(Waiting For Connection)**", quote=True
        )
        if LOG_CHANNEL:
            log = int(LOG_CHANNEL)
            op = await bot.send_message(
                log,
                f"[{message.from_user.first_name}](tg://user?id={message.from_user.id}) `Is Currently Downloading A Video…`",
            )
        s = dt.now()
        ttt = time.time()
        dir = f"downloads/"
        try:
            media_type = str(message.media)
            global download_task
            if media_type == "MessageMediaType.DOCUMENT":
                # if hasattr(event.media, "document"):
                # file = event.media.document
                # sem = event.message.message
                sem = message.caption
                ttx = Path("cap.txt")
                sen = message.document.file_name
                if sem and "\n" in sem:
                    sem = ""
                if sem and not ttx.is_file():
                    filename = sem
                else:
                    filename = sen
                if not filename:
                    filename = "video_" + dt.now().isoformat("_", "seconds") + ".mp4"
                root, ext = os.path.splitext(filename)
                if not ext:
                    ext = ".mkv"
                    filename = root + ext
                dl = dir + filename
                xxx = await xxx.edit("`Waiting For Download To Complete`")
                # tex = "`Downloading File 📶`"
                etch = await message.reply("`Downloading File 📂`", quote=True)
                # etch = await app.send_message(chat_id=message.from_user.id,
                # text=tex)
                download_task = asyncio.create_task(
                    app.download_media(
                        message=message,
                        file_name=dl,
                        progress=progress_for_pyrogram,
                        progress_args=(app, "`Downloading…`", etch, ttt),
                    )
                )
            else:
                sem = message.caption
                ttx = Path("cap.txt")
                if sem and "\n" in sem:
                    sem = ""
                if sem and not ttx.is_file():
                    filename = sem
                else:
                    filename = message.video.file_name
                if not filename:
                    filename = "video_" + dt.now().isoformat("_", "seconds") + ".mp4"
                root, ext = os.path.splitext(filename)
                if not ext:
                    ext = ".mkv"
                    filename = root + ext
                dl = dir + filename
                xxx = await xxx.edit("`Waiting For Media To Finish Downloading…`")
                # tex = "`Downloading Video 🎥`"
                # etch = await app.send_message(chat_id=message.from_user.id,
                # text=tex)
                etch = await message.reply("`Downloading Video 🎥`", quote=True)
                download_task = asyncio.create_task(
                    app.download_media(
                        message=message,
                        file_name=dl,
                        progress=progress_for_pyrogram,
                        progress_args=(app, "`Downloading…`", etch, ttt),
                    )
                )
            user = message.from_user.id
            USER_MAN.clear()
            USER_MAN.append(user)
            wah = code(dl)
            await app.get_users("me")
            dl_info = await parse_dl(filename)
            nnn = await event.reply(
                f"{enmoji()} `Downloading…`{dl_info}",
                buttons=[
                    [Button.inline("ℹ️", data=f"dl_stat{wah}")],
                    [Button.inline("CANCEL", data=f"cancel_dl{wah}")],
                ],
            )
            if LOG_CHANNEL:
                opp = await op.edit(
                    f"[{message.from_user.first_name}](tg://user?id={message.from_user.id}) `Is Currently Downloading A Video…`{dl_info}",
                    buttons=[
                        [Button.inline("ℹ️", data=f"dl_stat{wah}")],
                        [Button.inline("CANCEL", data=f"cancel_dl{wah}")],
                    ],
                )
            try:
                await download_task
            except Exception:
                pass
            if DOWNLOAD_CANCEL:
                canceller = await app.get_users(DOWNLOAD_CANCEL[0])
                await etch.edit(
                    f"Download of `{filename}` was cancelled by {canceller.mention(style='md')}."
                )
                await xxx.delete()
                await nnn.delete()
                if LOG_CHANNEL:
                    await op.edit(
                        f"[{message.from_user.first_name}'s](tg://user?id={message.from_user.id}) `download` was cancelled by [{canceller.first_name}.](tg://user?id={DOWNLOAD_CANCEL[0]})"
                    )
                DOWNLOAD_CANCEL.clear()
                WORKING.clear()
                return
        except Exception:
            WORKING.clear()
            er = traceback.format_exc()
            await channel_log(er)
            LOGS.info(er)
            return os.remove(dl)
        await etch.delete()
        es = dt.now()
        kk = dl.split("/")[-1]
        aa = kk.split(".")[-1]
        rr = f"encode"
        namo = dl.split("/")[1]
        if "v2" in namo:
            name = namo.replace("v2", "")
        else:
            name = namo
        bb1 = await parse(name, kk, aa)
        bb = bb1[0]
        bb2 = bb1[1]
        # if "'" in bb:
        # bb = bb.replace("'", "")
        out = f"{rr}/{bb}"
        b, d, c, rlsgrp = await dynamicthumb(name, kk, aa)
        tbcheck = Path("thumb2.jpg")
        if tbcheck.is_file():
            thum = "thumb2.jpg"
        else:
            thum = "thumb.jpg"
        with open("ffmpeg.txt", "r") as file:
            nani = file.read().rstrip()
            # ffmpeg = file.read().rstrip()
            file.close()
        try:
            if "This Episode" in nani:
                bo = b
                if d:
                    bo = f"Episode {d} of {b}"
                if c:
                    bo += f" Season {c}"
                nano = nani.replace(f"This Episode", bo)
            else:
                nano = nani
        except Exception:
            nano = nani
        if "Fileinfo" in nano:
            # bb = bb.replace("'", "")
            ffmpeg = nano.replace(f"Fileinfo", bb2)
        else:
            ffmpeg = nano
        dtime = ts(int((es - s).seconds) * 1000)
        e = xxx
        hehe = f"{out};{dl};0"
        wah = code(hehe)
        user = message.from_user.id
        xxx = await xxx.edit("`Waiting For Encoding To Complete`")
        # nn = await bot.send_message(
        #    user,
        nn = await nnn.edit(
            "`Encoding File(s)…` \n**⏳This Might Take A While⏳**",
            buttons=[
                [Button.inline("📂", data=f"pres{wah}")],
                [Button.inline("STATS", data=f"stats{wah}")],
                [Button.inline("CANCEL PROCESS", data=f"skip{wah}")],
            ],
        )
        try:
            qb = b.replace(" ", "_")
            for xob in [
                "\\",
                "",
                "*",
                "{",
                "}",
                "[",
                "]",
                "(",
                ")",
                ">",
                "#",
                "+",
                "-",
                ".",
                "!",
                "$",
                "/",
                ":",
            ]:
                if xob in qb:
                    qb = qb.replace(xob, "")
        except NameError:
            ob = bb.split("@")[0]
            qb = ob.replace(" ", "_")
            for xob in [
                "\\",
                "",
                "*",
                "{",
                "}",
                "[",
                "]",
                "(",
                ")",
                ">",
                "#",
                "+",
                "-",
                ".",
                "!",
                "$",
                "/",
                ":",
            ]:
                if xob in qb:
                    qb = qb.replace(xob, "")
        if LOG_CHANNEL:
            log = int(LOG_CHANNEL)
            oro = await bot.send_message(
                log,
                f"Encoding Of #{qb} Started By [{message.from_user.first_name}](tg://user?id={message.from_user.id})",
            )
            wak = await op.edit(
                f"[{message.from_user.first_name}](tg://user?id={message.from_user.id}) `Is Currently Encoding A Video…`",
                buttons=[
                    [Button.inline("ℹ️", data=f"pres{wah}")],
                    [Button.inline("CHECK PROGRESS", data=f"stats{wah}")],
                    [Button.inline("CANCEL PROCESS", data=f"skip{wah}")],
                ],
            )
        cmd = ffmpeg.format(dl, out)
        if ALLOW_ACTION is True:
            async with bot.action(message.from_user.id, "game"):
                process = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
        else:
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
        er = stderr.decode()
        try:
            if process.returncode != 0:
                if len(stderr) > 4095:
                    out_file = "ffmpeg_error.txt"
                    with open("ffmpeg_error.txt", "w") as file:
                        file.write(str(stderr.decode()))
                        wrror = await message.reply_document(
                            document=out_file,
                            force_document=True,
                            quote=True,
                            caption="`ffmpeg error`",
                        )
                    os.remove(out_file)
                else:
                    wrror = await message.reply(stderr.decode(), quote=True)
                WORKING.clear()
                try:
                    os.remove(dl)
                except Exception:
                    await wrror.reply("**Reason:** `Encoding Cancelled!`")
                await xxx.edit(f"🔺 **Encoding of** `{bb2}` **Failed**")
                if LOG_CHANNEL:
                    await wak.delete()
                return await nn.delete()
        except BaseException:
            er = traceback.format_exc()
            LOGS.info(er)
            await channel_log(er)
            LOGS.info(stderr.decode)
            await qclean()
            await xxx.edit("`An unknown error occurred.`")
            await nn.delete()
            if LOG_CHANNEL:
                await wak.delete()
            return WORKING.clear()
        ees = dt.now()
        ttt = time.time()
        try:
            await nn.delete()
            await wak.delete()
        except Exception:
            pass
        nnn = await xxx.edit("`▲ Uploading ▲`")
        fname = out.split("/")[1]
        # Check if Autogenerated thumbnail still exists
        if tbcheck.is_file():
            thum = "thumb2.jpg"
        else:
            thum = "thumb.jpg"
        pcap = await custcap(name, fname)
        ds = await upload2(message.from_user.id, out, nnn, thum, pcap, message)
        await nnn.delete()
        if FCHANNEL:
            chat = int(FCHANNEL)
            await ds.copy(chat_id=chat)
        if LOG_CHANNEL:
            chat = int(LOG_CHANNEL)
            await ds.copy(chat_id=chat)
        org = int(Path(dl).stat().st_size)
        com = int(Path(out).stat().st_size)
        pe = 100 - ((com / org) * 100)
        per = str(f"{pe:.2f}") + "%"
        eees = dt.now()
        x = dtime
        xx = ts(int((ees - es).seconds) * 1000)
        xxx = ts(int((eees - ees).seconds) * 1000)
        try:
            a1 = await info(dl, e)
            text = ""
            if rlsgrp:
                text += f"**Source:** `[{rlsgrp}]`"
            text += f"\n\nMediainfo: **[(Source)]({a1})**"
            dp = await ds.reply(
                text,
                disable_web_page_preview=True,
                quote=True,
            )
            if LOG_CHANNEL:
                await dp.copy(chat_id=chat)
        except Exception:
            pass
        dk = await ds.reply(
            f"**Encode Stats:**\n\nOriginal Size : {hbs(org)}\nEncoded Size : {hbs(com)}\nEncoded Percentage : {per}\n\nDownloaded in {x}\nEncoded in {xx}\nUploaded in {xxx}",
            disable_web_page_preview=True,
            quote=True,
        )
        if LOG_CHANNEL:
            await dk.copy(chat_id=chat)
        os.system("rm -rf thumb2.jpg")
        os.remove(dl)
        os.remove(out)
        WORKING.clear()
    except BaseException:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
        await qclean()
        WORKING.clear()
