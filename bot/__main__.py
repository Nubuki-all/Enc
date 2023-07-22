#    This file is part of the Compressor distribution.
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
# License can be found in
# <https://github.com/1Danish-00/CompressorQueue/blob/main/License> .


from pyrogram import filters

from . import *
from .devtools import *

LOGS.info("Starting...")


######## Connect ########


try:
    bot.start(bot_token=BOT_TOKEN)
    app.start()
except Exception as er:
    LOGS.info(er)


####### GENERAL CMDS ########


@bot.on(events.NewMessage(pattern="/start"))
async def _(e):
    await start(e)


@bot.on(events.NewMessage(pattern="/ping"))
async def _(e):
    await up(e)


@bot.on(events.NewMessage(pattern="/help"))
async def _(e):
    await help(e)


@bot.on(events.NewMessage(pattern="/restart"))
async def _(e):
    await restart(e)


@bot.on(events.NewMessage(pattern="/nuke"))
async def _(e):
    await nuke(e)


@bot.on(events.NewMessage(pattern="/cancelall"))
async def _(e):
    await clean(e)


@bot.on(events.NewMessage(pattern="/showthumb"))
async def _(e):
    await getthumb(e)


@bot.on(events.NewMessage(pattern=r"^/clear(\s+.+)?$"))
async def _(e):
    await clearqueue(e)


######## Callbacks #########


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"stats(.*)")))
async def _(e):
    await stats(e)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"pres(.*)")))
async def _(e):
    await pres(e)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"skip(.*)")))
async def _(e):
    await skip(e)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"dl_stat(.*)")))
async def _(e):
    await dl_stat(e)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"cancel_dl(.*)")))
async def _(e):
    await cancel_dl(e)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile("ihelp")))
async def _(e):
    await ihelp(e)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile("beck")))
async def _(e):
    await beck(e)


########## Direct ###########


@bot.on(events.NewMessage(pattern=r"^/eval([\s\S]*)$"))
async def _(e):
    await eval(e)


@bot.on(events.NewMessage(pattern=r"^/leech(\s+.+)?$"))
@bot.on(events.NewMessage(pattern=r"^/l(\s+.+)?$"))
async def _(e):
    await enleech(e)


@bot.on(events.NewMessage(pattern=r"^!dl(\s+.+)?$"))
async def _(e):
    await en_download(e)


@bot.on(events.NewMessage(pattern=r"^!ul(\s+.+)?$"))
async def _(e):
    await en_upload(e)


@bot.on(events.NewMessage(pattern=r"^!rename(\s+.+)?$"))
async def _(e):
    await en_rename(e)


@bot.on(events.NewMessage(pattern=r"^!mux\b([\s\S]*)"))
async def _(e):
    await en_mux(e)


@bot.on(events.NewMessage(pattern=r"^/permit(\s+.+)?$"))
async def _(e):
    await temp_auth(e)


@bot.on(events.NewMessage(pattern=r"^/unpermit(\s+.+)?$"))
async def _(e):
    await temp_unauth(e)


@app.on_message(filters.incoming & filters.command(["peval"]))
async def _(app, message):
    await eval_message_p(app, message)


@app.on_message(filters.incoming & filters.command(["update"]))
async def _(app, message):
    await update2(app, message)


@app.on_message(filters.incoming & filters.command(["fforward"]))
async def _(app, message):
    await fc_forward(message)


@bot.on(events.NewMessage(pattern="/bash"))
async def _(e):
    await bash(e)


@bot.on(events.NewMessage(pattern="/status"))
async def _(e):
    await status(e)


@bot.on(events.NewMessage(pattern=r"^/parse(\s+.+)?$"))
async def _(e):
    await discap(e)


@bot.on(events.NewMessage(pattern=r"^/v(\s+.+)?$"))
async def _(e):
    await version2(e)


@bot.on(events.NewMessage(pattern="/filter"))
async def _(e):
    await filter(e)


@bot.on(events.NewMessage(pattern="/vfilter"))
async def _(e):
    await vfilter(e)


@bot.on(events.NewMessage(pattern="/delfilter"))
async def _(e):
    await rmfilter(e)


@bot.on(events.NewMessage(pattern=r"^/name(\s+.+)?$"))
async def _(e):
    await auto_rename(e)


@bot.on(events.NewMessage(pattern=r"^/vname(\s+.+)?$"))
async def _(e):
    await v_auto_rename(e)


@bot.on(events.NewMessage(pattern=r"^/delname(\s+.+)?$"))
async def _(e):
    await del_auto_rename(e)


@bot.on(events.NewMessage(pattern="/reset"))
async def _(e):
    await reffmpeg(e)


@bot.on(events.NewMessage(pattern="/get"))
async def _(e):
    await check(e)


@bot.on(events.NewMessage(pattern="/set"))
async def _(e):
    await change(e)


@bot.on(events.NewMessage(pattern=r"^!queue$"))
@bot.on(events.NewMessage(pattern="/queue"))
async def _(e):
    await listqueue(e)


@bot.on(events.NewMessage(pattern=r"^/lock(\s+.+)?$"))
async def _(e):
    await lock(e)


@bot.on(events.NewMessage(pattern=r"^!queue -p([\s\S]*)$"))
async def _(e):
    await listqueuep(e)


@bot.on(events.NewMessage(pattern=r"^/groupenc(\s+.+)?$"))
async def _(e):
    await allowgroupenc(e)


@bot.on(events.NewMessage(pattern="/logs"))
async def _(e):
    await getlogs(e)


########## AUTO ###########


@bot.on(events.NewMessage(incoming=True))
async def _(e):
    await thumb(e)


@bot.on(events.NewMessage(incoming=True))
async def _(e):
    await encod(e)


@app.on_message(filters.incoming & (filters.video | filters.document))
async def _(app, message):
    await pencode(message)


async def something():
    await statuschecker()
    for i in itertools.count():
        try:
            while LOCKFILE:
                await asyncio.sleep(10)
            if QUEUE:
                while True:
                    queue_no = len(QUEUE)
                    await asyncio.sleep(1)
                    if len(QUEUE) > queue_no:
                        await asyncio.sleep(2)
                    else:
                        break
                # user = int(OWNER.split()[0])
                file = list(QUEUE.keys())[0]
                name, user = QUEUE[list(QUEUE.keys())[0]]
                uri = None
                try:
                    message = await app.get_messages(user, int(file))
                    mssg_r = await message.reply("`Download Pending…`", quote=True)
                    await asyncio.sleep(2)
                    e = await bot.send_message(
                        user,
                        "**[DEBUG]** `Preparing…`",
                        reply_to=mssg_r.id,
                    )
                    while True:
                        try:
                            await asyncio.sleep(2)
                            mssg_f = await (
                                await app.get_messages(e.chat_id, e.id)
                            ).edit("**[DEBUG]** `Waiting for download handler…`")
                            break
                        except pyro_errors.FloodWait as e:
                            await asyncio.sleep(e.value)
                except Exception:
                    LOGS.info(traceback.format_exc())
                    message = None
                    mssg_r = None
                    mssg_f = None
                    e = await bot.send_message(user, "`▼ Downloading…▼`")
                if message:
                    try:
                        user = message.from_user.id
                    except Exception:
                        pass
                if message:
                    s_user = 777000
                else:
                    s_user = OWNER.split()[0]
                if str(user).startswith("-100"):
                    user = s_user
                USER_MAN.clear()
                USER_MAN.append(user)
                sender = await app.get_users(user)
                if LOG_CHANNEL:
                    log = int(LOG_CHANNEL)
                    op = await bot.send_message(
                        log,
                        f"[{sender.first_name}](tg://user?id={user}) `Currently Downloading A Video…`",
                    )
                else:
                    op = None
                s = dt.now()
                try:
                    dl = "downloads/" + name
                    if message:
                        if message.text:
                            if message.text.startswith("/"):
                                uri = message.text.split(" ", maxsplit=1)[1].strip()
                            else:
                                uri = message.text

                    else:
                        if is_url(str(file)) is True:
                            uri = file
                    if CACHE_QUEUE:
                        raise (already_dl)
                    if message:
                        await mssg_r.edit("`Waiting for download to complete.`")
                    download = downloader(sender, op, uri=uri, dl_info=True)
                    downloaded = await download.start(dl, file, message, mssg_f)
                    if download.is_cancelled or download.download_error:
                        if message:
                            reply = f"Download of `{name}` "
                            if download.is_cancelled:
                                reply += "was cancelled"
                            else:
                                reply += "Failed"
                            if download.canceller:
                                if download.canceller.id != user:
                                    reply += (
                                        f" by {download.canceller.mention(style='md')}"
                                    )
                            reply += "!"
                            if download.download_error:
                                reply += f"\n`{download.download_error}`"
                            await mssg_r.edit(reply)
                        await e.delete()
                        if op:
                            if download.canceller:
                                await op.edit(
                                    f"[{sender.first_name}'s](tg://user?id={user}) `download was cancelled by` [{download.canceller.first_name}.](tg://user?id={download.canceller.id})"
                                )
                            else:
                                await op.edit(
                                    f"[{sender.first_name}'s](tg://user?id={user}) `download was cancelled."
                                )
                            if download.download_error:
                                await op.edit(
                                    f"[{sender.first_name}'s](tg://user?id={user}) `download failed!\n`{download.download_error}`"
                                )
                    if not downloaded or download.is_cancelled:
                        if QUEUE:
                            QUEUE.pop(list(QUEUE.keys())[0])
                        await save2db()
                        await qclean()
                        continue
                except already_dl:
                    if message:
                        await mssg_r.edit("`Waiting for caching to complete.`")
                    rslt = await get_cached(dl, sender, user, e, op)
                    if rslt is False:
                        await mssg_r.delete()
                        continue
                except Exception:
                    er = traceback.format_exc()
                    LOGS.info(er)
                    await channel_log(er)
                    QUEUE.pop(list(QUEUE.keys())[0])
                    await save2db()
                    continue
                es = dt.now()
                kk = dl.split("/")[-1]
                aa = kk.split(".")[-1]
                rr = "encode"
                name = dl.split("/")[-1]
                bb, bb2 = await parse(name, kk, aa)
                out = f"{rr}/{bb}"
                b, d, c, rlsgrp = await dynamicthumb(name)
                a_auto_disp = "-disposition:a auto"
                s_auto_disp = "-disposition:s auto"
                a_pos_in_stm, s_pos_in_stm = await pos_in_stm(dl)
                tbcheck = Path("thumb2.jpg")
                if tbcheck.is_file():
                    thum = "thumb2.jpg"
                else:
                    thum = "thumb.jpg"
                if uri and DUMP_LEECH is True:
                    asyncio.create_task(dumpdl(dl, name, thum, e.chat_id, message))
                if len(QUEUE) > 1 and CACHE_DL is True:
                    await cache_dl()
                with open("ffmpeg.txt", "r") as file:
                    # ffmpeg = file.read().rstrip()
                    nani = file.read().rstrip()
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
                except NameError:
                    nano = nani
                if "Fileinfo" in nano:
                    ffmpeg = nano.replace(f"Fileinfo", bb2)
                else:
                    ffmpeg = nano
                if a_auto_disp in ffmpeg:
                    if a_pos_in_stm or a_pos_in_stm == 0:
                        ffmpeg = ffmpeg.replace(
                            a_auto_disp,
                            f"-disposition:a 0 -disposition:a:{a_pos_in_stm} default",
                        )
                    else:
                        ffmpeg = ffmpeg.replace(a_auto_disp, "-disposition:a 0")
                if s_auto_disp in ffmpeg:
                    if s_pos_in_stm or s_pos_in_stm == 0:
                        ffmpeg = ffmpeg.replace(
                            s_auto_disp,
                            f"-disposition:s 0 -disposition:s:{s_pos_in_stm} default",
                        )
                    else:
                        ffmpeg = ffmpeg.replace(s_auto_disp, "-disposition:s 0")
                dtime = ts(int((es - s).seconds) * 1000)
                if uri:
                    name2, user2 = QUEUE[list(QUEUE.keys())[0]]
                    dl2 = "downloads/" + name2
                    hehe = f"{out};{dl2};{list(QUEUE.keys())[0]}"
                    wah2 = code(hehe)
                hehe = f"{out};{dl};{list(QUEUE.keys())[0]}"
                wah = code(hehe)
                if not uri:
                    wah2 = wah
                try:
                    if message:
                        await mssg_r.edit("`Waiting For Encoding To Complete`")
                except Exception:
                    pass
                nn = await e.edit(
                    "`Encoding File(s)…` \n**⏳This Might Take A While⏳**",
                    buttons=[
                        [Button.inline("📂", data=f"pres{wah2}")],
                        [Button.inline("STATS", data=f"stats{wah}")],
                        [Button.inline("CANCEL PROCESS", data=f"skip{wah}")],
                    ],
                )
                if LOG_CHANNEL:
                    wak = await op.edit(
                        f"[{sender.first_name}](tg://user?id={user}) `Is Currently Encoding a Video…`",
                        buttons=[
                            [Button.inline("📁", data=f"pres{wah2}")],
                            [Button.inline("CHECK PROGRESS", data=f"stats{wah}")],
                            [Button.inline("CANCEL PROCESS", data=f"skip{wah}")],
                        ],
                    )
                cmd = ffmpeg.format(dl, out)
                if ALLOW_ACTION is True:
                    async with bot.action(e.chat_id, "game"):
                        process = await asyncio.create_subprocess_shell(
                            cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await process.communicate()
                else:
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()
                er = stderr.decode()
                try:
                    if process.returncode != 0:
                        reply = f"Encoding of `{bb2}` "
                        if E_CANCEL:
                            reply += "was cancelled"
                        else:
                            reply += "Failed.\nLogs available below."
                        if E_CANCEL:
                            if E_CANCEL[0] != user:
                                canceller = await app.get_users(E_CANCEL[0])
                                if message:
                                    reply += f" by {canceller.mention(style='md')}"
                                else:
                                    reply += f" by [{canceller.first_name}.](tg://user?id={canceller.id})"
                            reply += "!"
                        if message:
                            await mssg_r.edit(reply)
                            if op:
                                await download.lm.edit(reply)
                        else:
                            await e.reply(reply)
                            if op:
                                await op.edit(reply)
                        await e.delete()
                        if len(er) > 4095 and not E_CANCEL:
                            yo = await app.send_message(
                                e.chat_id, "Uploading Error logs…"
                            )
                            out_file = "ffmpeg_error.txt"
                            with open(out_file, "w") as file:
                                file.write(er)
                            wrror = await yo.reply_document(
                                document=out_file,
                                force_document=True,
                                quote=True,
                                caption="`ffmpeg error`",
                            )
                            if op:
                                await wrror.copy(chat_id=int(LOG_CHANNEL))
                            await yo.delete()
                            os.remove(out_file)
                        elif not E_CANCEL:
                            await bot.send_message(int(user), stderr.decode())
                        if uri:
                            rm_leech_file(download.uri_gid)
                        else:
                            s_remove(dl)
                        s_remove(out)
                        if QUEUE:
                            QUEUE.pop(list(QUEUE.keys())[0])
                        E_CANCEL.clear()
                        await save2db()
                        continue
                except BaseException:
                    er = traceback.format_exc()
                    LOGS.info(er)
                    LOGS.info(stderr.decode())
                    await channel_log(er)
                    await nn.edit(
                        "An Unknown error occurred waiting for 30 seconds before trying again. "
                    )
                    if LOG_CHANNEL:
                        await wak.edit(
                            "An unknown error occurred waiting for 30 seconds before trying again."
                        )
                    await asyncio.sleep(30)
                    await qclean()
                    continue
                ees = dt.now()
                time.time()
                try:
                    await nn.delete()
                    await wak.delete()
                except Exception:
                    pass
                if message:
                    nnn = mssg_r
                else:
                    tex = "`▲ Uploading ▲`"
                    nnn = await app.send_message(chat_id=e.chat_id, text=tex)
                await asyncio.sleep(3)
                await enpause(nnn)
                fname = out.split("/")[1]
                tbcheck = Path("thumb2.jpg")
                if tbcheck.is_file():
                    thum = "thumb2.jpg"
                else:
                    thum = "thumb.jpg"
                pcap = await custcap(name, fname)
                upload = uploader(user)
                ds = await upload.start(e.chat_id, out, nnn, thum, pcap, message)
                if upload.is_cancelled:
                    await xxx.edit(f"`Upload of {out} was cancelled.`")
                    if LOG_CHANNEL:
                        log = int(LOG_CHANNEL)
                    canceller = await app.get_users(upload.canceller)
                    await bot.send_message(
                        log,
                        f"[{canceller.first_name}](tg://user?id={upload.canceller})`Cancelled` [{sender.first_name}'s](tg://user?id={user}) upload.",
                    )
                    QUEUE.pop(list(QUEUE.keys())[0])
                    await save2db()
                    os.system("rm -rf thumb2.jpg")
                    os.remove(dl)
                    os.remove(out)
                    continue
                await nnn.delete()
                if FCHANNEL:
                    chat = int(FCHANNEL)
                    if FBANNER:
                        try:
                            pic_id, f_msg = await f_post(name, out)
                            await app.send_photo(
                                photo=pic_id, caption=f_msg, chat_id=chat
                            )
                        except Exception:
                            pass
                    await ds.copy(chat_id=chat)
                    if FSTICKER:
                        try:
                            await app.send_sticker(
                                chat,
                                sticker=FSTICKER,
                            )
                        except Exception:
                            er = traceback.format_exc()
                            LOGS.info(er)
                            await channel_log(er)
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
                QUEUE.pop(list(QUEUE.keys())[0])
                await save2db()
                os.system("rm -rf thumb2.jpg")
                if uri:
                    rm_leech_file(download.uri_gid)
                else:
                    os.remove(dl)
                os.remove(out)
            else:
                await asyncio.sleep(3)
        except Exception:
            er = traceback.format_exc()
            LOGS.info(er)
            er = (
                er
                + "\n\nDue to the above fatal error bot has been locked to continue unlock bot."
            )
            await channel_log(er)
            for user in OWNER.split():
                try:
                    await bot.send_message(int(user), f"`{er}`")
                except Exception:
                    pass
            LOCKFILE.append("ERROR")


########### Start ############

LOGS.info("Bot has started.")
with bot:
    bot.loop.run_until_complete(startup())
    bot.loop.run_until_complete(something())
    bot.loop.run_forever()
