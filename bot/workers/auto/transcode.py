from os.path import split as path_split
from os.path import splitext as split_ext
from shutil import copy2 as copy_file

from bot import asyncio, ffmpeg_file, mux_file, pyro, tele, time
from bot.config import conf
from bot.others.exceptions import AlreadyDl
from bot.startup.before import entime
from bot.utils.ani_utils import custcap, dynamicthumb, f_post, parse, qparse_t
from bot.utils.batch_utils import (
    get_batch_list,
    get_downloadable_batch,
    mark_file_as_done,
)
from bot.utils.bot_utils import enc_canceller as e_cancel
from bot.utils.bot_utils import encode_info as einfo
from bot.utils.bot_utils import get_bqueue, get_queue, get_var, hbs
from bot.utils.bot_utils import time_formatter as tf
from bot.utils.db_utils import save2db
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    bc_msg,
    enpause,
    get_cached,
    reply_message,
    report_encode_status,
    report_failed_download,
)
from bot.utils.os_utils import file_exists, info, pos_in_stm, s_remove, size_of
from bot.workers.downloaders.dl_helpers import cache_dl
from bot.workers.downloaders.download import Downloader as downloader
from bot.workers.encoders.encode import Encoder as encoder
from bot.workers.uploaders.dump import dumpdl
from bot.workers.uploaders.upload import Uploader as uploader

thumb2 = "thumb2.jpg"


async def another(text, title, epi, sea, metadata, dl):
    a_auto_disp = "-disposition:a auto"
    s_auto_disp = "-disposition:s auto"
    a_pos_in_stm, s_pos_in_stm = await pos_in_stm(dl)

    if title:
        if "This Episode" in text:
            info = title
            if epi:
                info = f"Episode {epi} of {title}"
            if sea:
                info += f" Season {sea}"
            text = text.replace(f"This Episode", info)

    if "Fileinfo" in text:
        text = text.replace(f"Fileinfo", metadata)
    if a_auto_disp in text:
        if a_pos_in_stm or a_pos_in_stm == 0:
            text = text.replace(
                a_auto_disp,
                f"-disposition:a 0 -disposition:a:{a_pos_in_stm} default",
            )
        else:
            text = text.replace(a_auto_disp, "-disposition:a 0")
    if s_auto_disp in text:
        if s_pos_in_stm or s_pos_in_stm == 0:
            text = text.replace(
                s_auto_disp,
                f"-disposition:s 0 -disposition:s:{s_pos_in_stm} default",
            )
        else:
            text = text.replace(s_auto_disp, "-disposition:s 0")
    return text


async def forward_(name, out, ds, mi, f, ani):
    fb = conf.FBANNER
    fc = conf.FCHANNEL
    fs = conf.FSTICKER
    if not fc:
        return
    try:
        pic_id, f_msg = await f_post(name, out, ani, conf.FCODEC, mi, _filter=f, evt=fb)
        if pic_id:
            await pyro.send_photo(photo=pic_id, caption=f_msg, chat_id=fc)
    except Exception:
        await logger(Exception)
    await ds.copy(chat_id=fc)
    if not fs:
        return
    if not fb:
        queue = get_queue()
        bqueue = get_bqueue()
        queue_id = list(queue.keys())[0]
        if bqueue.get(queue_id):
            name, _none, v_f = list(queue.values())[0]
            blist = await get_batch_list(einfo._current, 1, v_f[0], v_f[1], parse=False)
            if blist:
                _pname = await qparse_t(einfo._current, v_f[0], v_f[1])
                _pname2 = await qparse_t(blist[0], v_f[0], v_f[1])
                if _pname == _pname2:
                    return

        elif len(queue) > 1:
            name, _none, v_f = list(queue.values())[0]
            name2, _none, v_f2 = list(queue.values())[1]
            _pname = await qparse_t(name, v_f[0], v_f[1])
            _pname2 = await qparse_t(name2, v_f2[0], v_f2[1])
            if _pname == _pname2:
                return
    try:
        await pyro.send_sticker(
            fc,
            sticker=fs,
        )
    except Exception:
        await logger(Exception)


def skip(queue_id):
    if einfo.batch:
        return
    bqueue = get_bqueue()
    queue = get_queue()
    try:
        bqueue.pop(queue_id)
    except Exception:
        pass
    try:
        queue.pop(queue_id)
    except Exception:
        pass


async def something():
    while True:
        await thing()
        # do some other stuff?


async def thing():
    try:
        while get_var("paused"):
            await asyncio.sleep(10)
        queue = get_queue()
        if not queue:
            await asyncio.sleep(1.5)
            return
        while True:
            queue_no = len(queue)
            await asyncio.sleep(2)
            if len(queue) == queue_no:
                break
            await asyncio.sleep(10)
        # user = int(OWNER.split()[0])
        queue_id = list(queue.keys())[0]
        chat_id, msg_id = queue_id
        download = None
        log_channel = conf.LOG_CHANNEL
        name, u_msg, v_f = list(queue.values())[0]
        v, f, m, n, au = v_f
        ani = au[0]
        einfo.uri = au[1]
        sender_id, message = u_msg
        if not message:
            message = await pyro.get_messages(chat_id, msg_id)
        else:
            message._client = pyro

        # Batches shenanigans
        if m[1].lower() == "batch.":
            einfo.batch = einfo.qbit = True
            file_name, index, name = get_downloadable_batch(queue_id)
            einfo.select = index
            n = None  # To prevent hell from breaking loose
            if name is None:
                einfo.batch = None
                skip(queue_id)
                await save2db()
                await save2db("batches")
                await asyncio.sleep(2)
                return

        try:
            msg_p = await message.reply("`Download Pending…`", quote=True)
        except Exception:
            msg_p = await pyro.send_message(chat_id, "`Download Pending…`")
            message = msg_p if einfo.uri else message
        await asyncio.sleep(2)
        msg_t = await tele.edit_message(
            chat_id, msg_p.id, "`Waiting for download handler…`"
        )

        _id = f"{msg_t.chat_id}:{msg_t.id}"
        if not sender_id or str(sender_id).startswith("-100"):
            sender_id = 777000
        sender = await pyro.get_users(sender_id)
        if chat_id == log_channel:
            await tele.send_message(
                log_channel,
                "**#WARNING: Logging disabled!**\nReason: `Encoding in log_channel`",
            )
            op = None
        elif log_channel:
            op = await tele.send_message(
                log_channel,
                f"[{sender.first_name}](tg://user?id={sender_id}) `Currently Downloading A Video…`",
            )
        else:
            op = None
        try:
            dl = "downloads/" + name
            if einfo.uri:
                if m[0] == "qbit":
                    einfo.qbit = True
                    if m[1].split()[0].lower() == "select.":
                        einfo.select = int(m[1].split()[1])

            if await cache_dl(check=True):
                raise (AlreadyDl)

            sdt = time.time()
            # await mssg_r.edit("`Waiting for download to complete.`")
            download = downloader(
                sender_id, op, _id, uri=einfo.uri, dl_info=True, qbit=einfo.qbit
            )
            download._sender = sender
            downloaded = await download.start(
                name, None, message, msg_p, select=einfo.select
            )
            if download.is_cancelled or download.download_error:
                f_msg = await report_failed_download(download, msg_p, name, sender_id)
                if op:
                    await pyro.edit_message_text(
                        log_channel,
                        op.id,
                        f"[{sender.first_name}'s](tg://user?id={sender_id}) "
                        + f_msg.text.markdown,
                    )
            if not downloaded or download.is_cancelled:
                skip(queue_id)
                mark_file_as_done(einfo.select, queue_id)
                await save2db()
                await save2db("batches")
                await asyncio.sleep(2)
                return
            dl = download.path
        except AlreadyDl:
            einfo.cached_dl = True
            msg_r = await reply_message(msg_p, "`Waiting for caching to complete.`")
            sdt = time.time()
            rslt = await get_cached(dl, sender, sender_id, msg_t, op)
            await msg_r.delete()
            if rslt is False:
                await msg_p.delete()
                await op.delete() if op else None
                return
        except Exception:
            await logger(Exception)
            skip(queue_id)
            mark_file_as_done(einfo.select, queue_id)
            await save2db()
            await save2db("batches")
            return
        edt = time.time()
        dtime = tf(edt - sdt)

        d_folder, d_fname = path_split(dl)
        d_ext = split_ext(d_fname)[-1]
        _dir = "encode"
        file_name, metadata_name = await parse(
            name,
            d_fname,
            d_ext,
            anilist=ani,
            v=v,
            folder=d_folder,
            _filter=f,
            direct=n,
        )
        out = f"{_dir}/{file_name}"
        title, epi, sn, rlsgrp = await dynamicthumb(
            name, anilist=(not n or ani), _filter=f
        )

        c_n = f"{title} {sn or str()}".strip()
        if einfo.previous and einfo.previous == c_n:
            pass
        else:
            einfo.previous = c_n
            for x in ("!", ":", ";", "-", " "):
                c_n = c_n.replace(x, "_")
            await op.reply("#" + c_n) if op else None
            await msg_p.reply("#" + c_n) if log_channel == chat_id else None
        if einfo.uri and conf.DUMP_LEECH is True:
            asyncio.create_task(dumpdl(dl, name, thumb2, msg_t.chat_id, message))
        if len(queue) > 1 and conf.CACHE_DL and not einfo.batch:
            await cache_dl()
        with open(ffmpeg_file, "r") as file:
            nani = file.read().rstrip()
        ffmpeg = await another(nani, title, epi, sn, metadata_name, dl)

        _set = time.time()
        einfo.current = file_name
        einfo._current = name
        cmd = ffmpeg.format(dl, out)
        encode = encoder(_id, sender, msg_t, op)
        # await mssg_r.edit("`Waiting For Encoding To Complete`")
        await encode.start(cmd)
        await encode.callback(dl, out, msg_t, sender_id, stime=_set)
        stdout, stderr = await encode.await_completion()
        await report_encode_status(
            encode.process,
            _id,
            stderr,
            msg_t,
            sender_id,
            out,
            log_msg=op,
            stdout=stdout,
            exe_prefix=ffmpeg.split(maxsplit=1)[0],
        )
        if encode.process.returncode != 0:
            if download:
                await download.clean_download()
            s_remove(out)
            skip(queue_id)
            mark_file_as_done(einfo.select, queue_id)
            e_cancel().pop(_id) if e_cancel().get(_id) else None
            await save2db()
            await save2db("batches")
            return
        eet = time.time()
        etime = tf(eet - _set)

        await asyncio.sleep(3)
        await enpause(msg_p)

        mux_args = None
        if file_exists(mux_file):
            with open(mux_file, "r") as file:
                mux_args = file.read().rstrip("\n").rstrip()
            smt = time.time()
            mux_args = await another(mux_args, title, epi, sn, metadata_name, dl)
            ffmpeg = 'ffmpeg -i """{}""" ' f"{mux_args} -codec copy" ' """{}""" -y'
            _out = split_ext(out)[0] + " [Muxing]" + split_ext(out)[1]
            cmd = ffmpeg.format(out, _out)
            encode = encoder(_id, event=msg_t)
            await encode.start(cmd)
            stderr = (await encode.await_completion())[1]
            await report_encode_status(
                encode.process,
                _id,
                stderr,
                msg_t,
                sender_id,
                out,
                _is="Muxing",
                log_msg=op,
            )
            if encode.process.returncode != 0:
                if download:
                    await download.clean_download()
                s_remove(out, _out)
                skip(queue_id)
                mark_file_as_done(einfo.select, queue_id)
                e_cancel().pop(_id) if e_cancel().get(_id) else None
                await save2db()
                await save2db("batches")
                return
            s_remove(out)
            copy_file(_out, out)
            s_remove(_out)
            emt = time.time()
            mtime = tf(emt - smt)

        sut = time.time()
        fname = path_split(out)[1]
        pcap = await custcap(
            name, fname, anilist=ani, ver=v, encoder=conf.ENCODER, _filter=f, direct=n
        )
        await op.edit(f"`Uploading…` `{out}`") if op else None
        upload = uploader(sender_id, _id)
        up = await upload.start(msg_t.chat_id, out, msg_p, thumb2, pcap, message)
        if upload.is_cancelled:
            m = f"`Upload of {out} was cancelled`"
            if sender_id != upload.canceller:
                canceller = await pyro.get_users(upload.canceller)
                # m += f"by [{canceller.first_name}](tg://user?id={upload.canceller})"
                m += f"by {canceller.mention()}"
            m += "!"
            await msg_p.edit(m)
            if op:
                await op.edit(m)
            skip(queue_id)
            mark_file_as_done(einfo.select, queue_id)
            await save2db()
            await save2db("batches")
            if download:
                await download.clean_download()
            s_remove(thumb2, dl, out)
            return
        eut = time.time()
        utime = tf(eut - sut)

        await msg_p.delete()
        await op.delete() if op else None
        await up.copy(chat_id=log_channel) if op else None

        org_s = size_of(dl)
        out_s = size_of(out)
        pe = 100 - ((out_s / org_s) * 100)
        per = str(f"{pe:.2f}") + "%"
        mux_msg = f"Muxed in `{mtime}`\n" if mux_args else str()

        text = str()
        mi = await info(dl)
        forward_task = asyncio.create_task(forward_(name, out, up, mi, f, ani))

        text += f"**Source:** `[{rlsgrp}]`"
        if mi:
            text += f"\n\nMediainfo: **[(Source)]({mi})**"
        mi_msg = await up.reply(
            text,
            disable_web_page_preview=True,
            quote=True,
        )
        await mi_msg.copy(chat_id=log_channel) if op else None

        st_msg = await up.reply(
            f"**Encode Stats:**\n\nOriginal Size: "
            f"`{hbs(org_s)}`\nEncoded Size: `{hbs(out_s)}`\n"
            f"Encoded Percentage: `{per}`\n\n"
            f"{'Cached' if einfo.cached_dl else 'Downloaded'} in `{dtime}`\n"
            f"Encoded in `{etime}`\n{mux_msg}Uploaded in `{utime}`",
            disable_web_page_preview=True,
            quote=True,
        )
        await st_msg.copy(chat_id=log_channel) if op else None
        await forward_task

        skip(queue_id)
        mark_file_as_done(einfo.select, queue_id)
        await save2db()
        await save2db("batches")
        s_remove(thumb2)
        if download:
            await download.clean_download()
        s_remove(dl, out)

    except Exception:
        await logger(Exception)
        error = (
            "Due to an unknown error "
            "bot has been paused indefinitely\n"
            "check logs for more info."
        )
        l_msg = await bc_msg(error)
        entime.pause_indefinitely(l_msg)

    finally:
        einfo.reset()
        await asyncio.sleep(5)
