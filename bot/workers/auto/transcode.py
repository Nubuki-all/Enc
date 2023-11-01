from bot import Path, asyncio, pyro, tele, time
from bot.config import CACHE_DL as cache
from bot.config import DUMP_LEECH as dump
from bot.config import ENCODER
from bot.config import FBANNER as fb
from bot.config import FCHANNEL as fc
from bot.config import FCODEC
from bot.config import FSTICKER as fs
from bot.config import LOG_CHANNEL as log_channel
from bot.others.exceptions import AlreadyDl
from bot.startup.before import entime
from bot.utils.ani_utils import custcap, dynamicthumb, f_post, parse, qparse_t
from bot.utils.bot_utils import CACHE_QUEUE as cached
from bot.utils.bot_utils import LAST_ENCD as l_enc
from bot.utils.bot_utils import E_CANCEL, get_queue, get_var, hbs
from bot.utils.bot_utils import time_formatter as tf
from bot.utils.db_utils import save2db
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    bc_msg,
    enpause,
    get_args,
    get_cached,
    reply_message,
    report_encode_status,
    report_failed_download,
)
from bot.utils.os_utils import info, pos_in_stm, s_remove
from bot.workers.downloaders.dl_helpers import cache_dl, rm_leech_file
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


async def forward_(name, out, ds, mi, f):
    if not fc:
        return
    if fb:
        try:
            pic_id, f_msg = await f_post(name, out, FCODEC, mi, _filter=f)
            await pyro.send_photo(photo=pic_id, caption=f_msg, chat_id=fc)
        except Exception:
            await logger(Exception)
    await ds.copy(chat_id=fc)
    if not fs:
        return
    if not fb:
        queue = get_queue()
        if len(queue) > 1:
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


async def something():
    while True:
        await thing()
        # do some other stuff?


async def thing():
    try:
        while get_var("pausefile"):
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
        chat_id, msg_id = list(queue.keys())[0]
        name, u_msg, v_f = list(queue.values())[0]
        # backward compability:
        if not isinstance(v_f, tuple):
            v, f = v_f, None
        else:
            v, f = v_f
        sender_id, message = u_msg
        if not message:
            message = await pyro.get_messages(chat_id, msg_id)
        else:
            message._client = pyro
        cached_dl = False
        uri = None
        msg_p = await message.reply("`Download Pending…`", quote=True)
        await asyncio.sleep(2)
        msg_t = await tele.edit_message(
            chat_id, msg_p.id, "`Waiting for download handler…`"
        )
        # USER_MAN.clear()
        # USER_MAN.append(user)
        _id = f"{msg_t.chat_id}:{msg_t.id}"
        if str(sender_id).startswith("-100"):
            sender_id = 777000
        sender = await pyro.get_users(sender_id)
        if chat_id == log_channel:
            await tele.send_message(log_channel, "**#WARNING: Logging disabled!**\nReason: `Encoding in log_channel`")
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
            if message.text:
                if message.text.startswith("/"):
                    uri = message.text.split(" ", maxsplit=1)[1].strip()
                else:
                    uri = message.text
                uri = get_args(
                    "-f", "-rm", "-tc", "-tf", "-v", to_parse=uri, get_unknown=True
                )[1]

            if cached:
                raise (AlreadyDl)

            sdt = time.time()
            # await mssg_r.edit("`Waiting for download to complete.`")
            download = downloader(sender_id, op, _id, uri=uri, dl_info=True)
            download._sender = sender
            downloaded = await download.start(name, None, message, msg_p)
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
                if queue:
                    queue.pop(list(queue.keys())[0])
                await save2db()
                await asyncio.sleep(2)
                return
        except AlreadyDl:
            cached_dl = True
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
            queue.pop(list(queue.keys())[0])
            await save2db()
            return
        edt = time.time()
        dtime = tf(edt - sdt)

        kk = dl.split("/")[-1]
        aa = kk.split(".")[-1]
        _dir = "encode"
        file_name, metadata_name = await parse(name, kk, aa, v=v, _filter=f)
        out = f"{_dir}/{file_name}"
        title, epi, sn, rlsgrp = await dynamicthumb(name, _filter=f)

        if l_enc and l_enc[0]  == (c_n := f"{title} {sn}".strip()):
            pass
        else:
            l_enc.clear()
            l_enc.append(c_n)
            for x in ("!", ":", "-", " "):
                c_n = c_n.replace(x, "_")
            await op.reply("#" + c_n) if op else None
            await msg_p.reply("#" + c_n) if log_channel == chat_id else None
        if uri and dump is True:
            asyncio.create_task(dumpdl(dl, name, thumb2, msg_t.chat_id, message))
        if len(queue) > 1 and cache:
            await cache_dl()
        with open("ffmpeg.txt", "r") as file:
            nani = file.read().rstrip()
        ffmpeg = await another(nani, title, epi, sn, metadata_name, dl)

        _set = time.time()
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
        )
        if encode.process.returncode != 0:
            if uri:
                rm_leech_file(download.uri_gid)
            else:
                s_remove(dl)
            s_remove(out)
            if queue:
                queue.pop(list(queue.keys())[0])
            E_CANCEL.pop(_id) if E_CANCEL.get(_id) else None
            await save2db()
            return
        eet = time.time()
        etime = tf(eet - _set)

        await asyncio.sleep(3)
        await enpause(msg_p)

        sut = time.time()
        fname = out.split("/")[1]
        pcap = await custcap(name, fname, ver=v, encoder=ENCODER, _filter=f)
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
            queue.pop(list(queue.keys())[0])
            await save2db()
            if uri:
                rm_leech_file(download.uri_gid)
            s_remove(thumb2, dl, out)
            return
        eut = time.time()
        utime = tf(eut - sut)

        await msg_p.delete()
        await op.delete() if op else None
        await up.copy(chat_id=log_channel) if log_channel else None

        org_s = int(Path(dl).stat().st_size)
        out_s = int(Path(out).stat().st_size)
        pe = 100 - ((out_s / org_s) * 100)
        per = str(f"{pe:.2f}") + "%"

        text = str()
        mi = await info(dl)
        await forward_(name, out, up, mi, f)

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
            f"{"Cached" if cached_dl else "Downloaded"} in `{dtime}`\n"
            f"Encoded in `{etime}`\nUploaded in `{utime}`",
            disable_web_page_preview=True,
            quote=True,
        )
        await st_msg.copy(chat_id=log_channel) if op else None

        queue.pop(list(queue.keys())[0])
        await save2db()
        s_remove(thumb2)
        if uri:
            rm_leech_file(download.uri_gid)
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
        await asyncio.sleep(5)
