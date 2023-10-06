import os
import shutil

from bot import (
    Button,
    asyncio,
    home_dir,
    itertools,
    log_file_name,
    pyro_errors,
    thumb,
    time,
)
from bot.fun.emojis import enmoji
from bot.utils.ani_utils import custcap, dynamicthumb, parse
from bot.utils.bot_utils import (
    code,
    get_f,
    get_filename,
    is_magnet,
    is_url,
    u_cancelled,
    video_mimetype,
)
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    get_args,
    get_message_from_link,
    report_encode_status,
    report_failed_download,
    try_delete,
    turn,
    user_is_allowed,
    user_is_dev,
    user_is_owner,
    wait_for_turn,
    waiting_for_turn,
)
from bot.utils.os_utils import (
    check_ext,
    dir_exists,
    file_exists,
    pos_in_stm,
    s_remove,
    size_of,
)
from bot.workers.downloaders.dl_helpers import get_leech_name, rm_leech_file
from bot.workers.downloaders.download import Downloader as downloader
from bot.workers.encoders.encode import Encoder as encoder
from bot.workers.uploaders.upload import Uploader as uploader

thumb3 = "thumb3.jpg"
aria2_err_msg = "`An error with aria2 occurred`"
not_vid_msg = "`Batches and Non-videos not supported`"


async def getlogs(event, args, client):
    """Upload bots logs in txt format."""
    user = event.sender_id
    if not (user_is_dev(user) or user_is_owner(user)):
        return await event.delete()
    await event.reply(file=log_file_name, force_document=True)


async def getthumb(event, args, client):
    """Dumps all available thumbnails"""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    thumb2 = "thumb2.jpg"
    thumbs = []
    for thum in (thumb, thumb2, thumb3):
        if file_exists(thum):
            thumbs.append(thum)

    for thum, no in zip(thumbs, itertools.count(1)):
        cap = f"**Your Current Thumbnail. #{no}**"
        await event.client.send_file(
            event.chat_id,
            file=thum,
            force_document=False,
            caption=cap,
        )


async def en_download(event, args, client):
    """
    Downloads the replied message: to a location (specified) locally
    Available arguments:
      End the args with '/' to specify the folder in which to download and let the bot use its filename
      or:
        --dir DIR (Must be in double quotes.)
        --home (To download to current working directory.)
      --cap (To use download with caption instead of filename.)
      if no other arg is given after dir, bot automatically downloads to given dir with default filename instead.

      *path specified directly will be downloaded to download folder
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    if not event.is_reply:
        return await event.reply("`Reply to a file or link to download it`")
    try:
        _dir = None
        loc = None
        link = None
        rep_event = await event.get_reply_message()
        message = await client.get_messages(event.chat_id, int(rep_event.id))
        if message.text and not (is_url(message.text) or is_magnet(message.text)):
            return await message.reply("`Not a valid link`")
        e = await message.reply(f"{enmoji()} `Downloading…`", quote=True)
        if args is not None:
            arg, args = get_args(
                ["--home", "store_true"],
                ["--cap", "store_true"],
                "--dir",
                to_parse=args,
                get_unknown=True,
            )
            if args.endswith("/"):
                _dir = args
            elif arg.home:
                _dir = home_dir
            elif arg.dir:
                _dir = arg.dir
            if arg.cap and not message.text:
                loc = message.caption
            else:
                loc = args
        link = message.text if message.text else link
        if not loc:
            loc = rep_event.file.name if not link else link
        _dir = "downloads/" if not _dir else _dir
        _dir += str() if _dir.endswith("/") else "/"
        await try_delete(event)
        download = downloader(uri=link, folder=_dir)
        await download.start(loc, 0, message, e)
        if download.is_cancelled or download.download_error:
            return await report_failed_download(download, e, loc, event.sender_id)
        f_loc = _dir + loc if not link else _dir + download.file_name
        await e.edit(f"__Saved to__ `{f_loc}` __successfully!__")
    except Exception:
        await logger(Exception)


async def en_rename(event, args, client):
    """
    Reply to a file/link to download,rename and upload it.

    Available flags:
    -np - disables anilist parsing.
    -e {emoji} customize emoji in caption
    -q {quality} quality in codec
    -tc {caption type} specify type in caption
    -tf {file tag} specify file language tag.
    -v {int} specify a number for versionimg

    To define file name send any of the below as arguments:
    "file_name" > str - custom name to rename to (if parsing is enabled this is parsed too)
    0 > int - get file name from caption.
    """
    turn_id = f"{event.chat_id}:{event.id}"
    user = event.sender_id
    if not user_is_owner(user):
        return await event.delete()
    if not event.is_reply:
        return await event.reply("`Reply to a file to rename it`")
    try:
        download = None
        link = None
        _parse = True
        work_folder = "temp/"
        _em = _q = _tc = _tf = _v = None
        rep_event = await event.get_reply_message()
        message = await client.get_messages(event.chat_id, int(rep_event.id))
        if message.text and not (is_url(message.text) or is_magnet(message.text)):
            return await message.reply("`Not a valid link.`")
        elif not (message.text or message.document or message.video):
            return await message.reply("`Kindly Reply to a link/video.`")
        link = message.text if message.text else None
        if args:
            arg, args = get_args(
                ["-np", "store_false"],
                "-e",
                "-q",
                "-tc",
                "-tf",
                "-v",
                to_parse=args,
                get_unknown=True,
            )
            _parse = arg.np
            _em = arg.e
            _q = arg.q
            _tc = arg.tc
            _tf = arg.tf
            _v = arg.v
        if not args and not link:
            loc = rep_event.file.name
        elif args == "0" and not link:
            loc = message.caption
        elif not link:
            loc = check_ext(args)
        if not link:
            __loc = loc
            __out, __none = await parse(loc, anilist=_parse, folder=work_folder)
        else:
            __out = await get_leech_name(link)
            if not __out:
                error = aria2_err_msg if __out is None else not_vid_msg
                return await rep_event.reply(error)
            if __out.startswith("aria2_error"):
                error = __out.split("aria2_error")[1].strip()
                return await rep_event.reply(f"`{error}`")
            __loc = __out
        _f = get_f()
        turn().append(turn_id)
        if waiting_for_turn():
            w_msg = await message.reply(
                "`Waiting till previous process gets completed.`", quote=True
            )
            await wait_for_turn(turn_id, w_msg)
        loc = __out
        e = await message.reply(f"{enmoji()} `Downloading to {loc}…`", quote=True)
        await asyncio.sleep(5)
        download = downloader(uri=link, folder=work_folder)
        downloaded = await download.start(loc, 0, message, e)
        if download.is_cancelled or download.download_error:
            return await report_failed_download(download, e, __out, user)
        loc = work_folder + __out
        await e.edit(f"Downloading to `{loc}` completed.")
        __pout, __pout1 = await parse(
            __loc,
            __out,
            anilist=_parse,
            folder=work_folder,
            cust_con=_tf,
            v=_v,
            _filter=_f,
            ccodec=_q,
        )
        if not __pout == __out:
            await asyncio.sleep(3)
            await e.edit(f"Renaming:\n`{__out}`\n >>>\n`{__pout}`…")
            ploc = work_folder + __pout
            shutil.copy2(loc, ploc)
            s_remove(loc)
            loc = ploc
            __out = __pout
        await asyncio.sleep(5)
        thumb3 = "thumb3.jpg"
        await dynamicthumb(__loc, thumb3, anilist=_parse, _filter=_f)
        cap = await custcap(
            __loc,
            __out,
            anilist=_parse,
            cust_type=_tc,
            folder=work_folder,
            ccd=_em,
            ver=_v,
            _filter=_f,
            ccodec=_q,
        )
        upload = uploader(event.sender_id)
        await upload.start(event.chat_id, loc, e, thumb3, cap, message)
        if not upload.is_cancelled:
            await e.edit(f"`{__out}` __uploaded successfully.__")
        else:
            await e.edit(f"__Upload of__ `{__out}` was cancelled.__")
        s_remove(thumb3, loc)
    except Exception:
        await logger(Exception)
    finally:
        if turn(turn_id):
            turn().pop(0)
        if link and download and downloaded:
            rm_leech_file(download.uri_gid)


async def en_mux(event, args, client):
    """
    Remuxes/encodes a replied video/link
        - Does not recover from database during restart
    Required arguments:
        valid ffmpeg parameters without the 'ffmpeg', '-i' or output
    Optional arguments:
        All optional arguments are passed seperated from the required argument with a newline
        -i {link of file to download, tg link also supported(must be a supergroup link to file)}
        -np to turn off anilist
        -d {file_name} to change download name
        -c to delete command after muxing - needs no argument.
        -v tag files with versions.
        -q custom caption codec
        -default_a {lang_iso3} iso3 of the audio language to default.
            if there are multiple matching languages the first is selected.
        -default_s {lang_iso3} same as above but for subtitles.
            the probability of this working rests on the source file having a language metadata.
        -ext {ext} force change extension (requires the preceding dot ".")
        -tag_c {string} force tag caption
        -tag_f {string} force tag file
    """

    turn_id = f"{event.chat_id}:{event.id}"
    user = event.sender_id
    if not user_is_owner(user):
        return await event.delete()
    if not event.is_reply:
        return await event.reply("`Reply to a file to remux it`")
    try:
        # ref vars.

        ani_parse = True
        codec = None
        default_audio = None
        default_sub = None
        download = download2 = None
        flags = None
        input_2 = None
        link = None
        ver = None
        work_folder = "mux/"
        cap_tag = file_tag = force_ext = None

        rep_event = await event.get_reply_message()
        message = await client.get_messages(event.chat_id, int(rep_event.id))
        if message.document:
            if message.document.mime_type not in video_mimetype:
                return
        elif message.text:
            if not (is_url(message.text) or is_magnet(message.text)):
                return await message.reply("`Invalid Link.`")
            link = message.text
        elif not message.video:
            return
        if args is None:
            return await event.reply(
                "__ffmpeg muxing parameters are required as arguments__"
            )

        name = get_filename(message) if not link else await get_leech_name(link)
        if not name:
            error = aria2_err_msg if name is None else not_vid_msg
            return await rep_event.reply(error)
        if name.startswith("aria2_error"):
            error = input_2.split("aria2_error")[1].strip()
            return await rep_event.reply(f"{error}")
        if "\n" in args:
            args, flags = args.split("\n", maxsplit=1)
            flag = get_args(
                ["-c", "store_true"],
                "-d",
                "-default_a",
                "-default_s",
                "-ext",
                "-i",
                ["-np", "store_true"],
                "-q",
                "-tag_c",
                "-tag_f",
                "-v",
                to_parse=flags,
            )
            if flag.np:
                ani_parse = False
            if flag.i and (is_url(flag.i) or is_magnet(flag.i)):
                link2 = None
                if flag.i.startswith("https://t.me"):
                    message_2 = await get_message_from_link(flag.i)
                    if not message_2:
                        return await event.reply(
                            "An error occurred while fetching second input."
                        )
                    if not message_2.video and not message_2.document:
                        return await event.reply(
                            "Second input is not a video/document."
                        )
                    name_2 = get_filename(message_2)
                else:
                    link2 = flag.i
                    message_2 = None
                    name_2 = await get_leech_name(link2)
                    if not name_2:
                        error = aria2_err_msg if __out is None else not_vid_msg
                        return await event.reply(error)
                    if name_2.startswith("aria2_error"):
                        error = name_2.split("aria2_error")[1].strip()
                        return await event.reply(f"{error}")
                input_2 = work_folder + name_2
            cap_tag = flag.tag_c
            codec = flag.q
            default_audio = flag.default_a
            default_sub = flag.default_s
            file_tag = flag.tag_f
            force_ext = flag.ext
            name = flag.d or name
            ver = flag.v

        name, root, ext = check_ext(name, get_split=True)
        _f = get_f()
        ext = force_ext or ext
        __loc = name
        dl = work_folder + name
        turn().append(turn_id)
        if waiting_for_turn():
            w_msg = await message.reply(
                "`Waiting for previous process to complete.`", quote=True
            )
            await wait_for_turn(turn_id, w_msg)
        e = await message.reply(f"{enmoji()} `Downloading to {dl}…`", quote=True)
        await asyncio.sleep(5)
        download = downloader(uri=link, folder=work_folder)
        downloaded = await download.start(name, 0, message, e)
        if download.is_cancelled or download.download_error:
            s_remove(dl)
            return await report_failed_download(download, e, name, user)
        await e.edit(f"Download to `{dl}` completed.")
        if input_2:
            await asyncio.sleep(3)
            await e.edit(f"{enmoji()} `Downloading second input to {input_2}…`")
            await asyncio.sleep(5)
            download2 = downloader(uri=link2, folder=work_folder)
            downloaded2 = await download2.start(name_2, 0, message_2, e)
            if download2.is_cancelled or download2.download_error:
                s_remove(dl)
                return await report_failed_download(download2, e, name_2, user)
            await e.edit(f"Download to `{input_2}` completed.")

        await e.delete()
        e = await event.reply("`…`")
        t_file = work_folder + root + " [Temp]" + ext
        args = args.strip()
        args = f'-i "{input_2}" ' + args if input_2 else args
        await asyncio.sleep(3)
        text = "**Currently Muxing:**\n└`{}`\n\n`using provided parameters…`"
        cmd = f'''ffmpeg -i """{dl}""" {args} """{t_file}""" -y'''
        e_id = f"{e.chat_id}:{e.id}"
        stime = time.time()
        encode = encoder(e_id, event=event)
        await encode.start(cmd)
        await encode.callback(dl, t_file, e, user, text, stime)
        stderr = (await encode.await_completion())[1]
        await report_encode_status(
            encode.process, e_id, stderr, e, user, t_file, _is="Muxing"
        )
        if encode.process.returncode != 0:
            s_remove(dl, t_file)
            return
        __out, __out1 = await parse(
            name,
            t_file.split("/")[-1],
            anilist=ani_parse,
            cust_con=file_tag,
            v=ver,
            folder=work_folder,
            _filter=_f,
            ccodec=codec,
        )
        loc = work_folder + __out
        b, d, c, rlsgrp = await dynamicthumb(
            __loc, thumb3, anilist=ani_parse, _filter=_f
        )
        args2 = ""
        for arg in args.split("-"):
            if "metadata" in arg:
                args2 += "-" + arg + " "
        if "This Episode" in args2:
            bo = b
            if d:
                bo = f"Episode {d} of {b}"
            if c:
                bo += f" Season {c}"
            args2 = args2.replace(f"This Episode", bo)
        if "Fileinfo" in args2:
            args2 = args2.replace("Fileinfo", __out1)
        args2 = args2.strip()
        if default_audio:
            args2 += f" -disposition:a 0"
            a_pos_in_stm = await pos_in_stm(t_file, default_audio, get="audio")
            if a_pos_in_stm or a_pos_in_stm == 0:
                args2 += f" -disposition:a:{a_pos_in_stm} default"
        if default_sub:
            args2 += f" -disposition:s 0"
            s_pos_in_stm = await pos_in_stm(t_file, default_sub, get="sub")
            if s_pos_in_stm or s_pos_in_stm == 0:
                args2 += f" -disposition:s:{s_pos_in_stm} default"
        cmd = f'ffmpeg -i "{t_file}" -map 0:v? -map 0:a? -map 0:s? -map 0:t? {args2} -codec copy "{loc}" -y'
        encode = encoder(e_id, event=event)
        await encode.start(cmd)
        stderr = (await encode.await_completion())[1]
        await report_encode_status(
            encode.process, e_id, stderr, e, user, loc, _is="Editing metadata"
        )
        if encode.process.returncode != 0:
            s_remove(dl, t_file, loc)
            return
        cap = await custcap(
            __loc,
            __out,
            anilist=ani_parse,
            cust_type=cap_tag,
            folder=work_folder,
            ver=ver,
            _filter=_f,
            ccodec=codec,
        )
        await asyncio.sleep(5)
        upload = uploader(user)
        await upload.start(event.chat_id, loc, e, thumb3, cap, message)
        if not upload.is_cancelled:
            await e.edit(f"`{__out}` __uploaded successfully.__")
        else:
            await e.edit(f"__Upload of__ `{__out}` __was cancelled.__")
        if flags and flag.c:
            await try_delete(event)
        s_remove(dl, t_file, loc)
    except Exception:
        await logger(Exception)
    finally:
        if turn(turn_id):
            turn().pop(0)
        if download and downloaded:
            rm_leech_file(download.uri_gid)
        if download2 and downloaded2:
            rm_leech_file(download2.uri_gid)
        if input_2:
            s_remove(input_2)
        s_remove(thumb3)


async def en_upload(event, args, client):
    """
    Uploads a file/files from local directory or direct/torrent link
    Just pass any of the following:
        - the file (with -f) e.g -f "something.txt"
        - the folder path
        - direct link
        - torrent/magnet link
        as argument.
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        download = None
        uri = None
        u_can_msg = "`Folder upload has been force cancelled`"
        message = await client.get_messages(event.chat_id, int(event.id))
        file = args
        chain_msg = message
        arg = get_args("-f", to_parse=args)
        if arg.f:
            file = arg.f
        elif is_url(args) or is_magnet(args):
            folder, uri = "downloads2/", True
            dl = await message.reply(
                "`Preparing to download file from link…`",
                quote=True,
            )
            download = downloader(uri=args, folder=folder)
            downloaded = await download.start(None, None, True, dl)
            if download.is_cancelled or download.download_error:
                return await report_failed_download(
                    download, dl, download.file_name, event.sender_id
                )
            await dl.delete()
            file = folder + downloaded.name
        if not file_exists(file) and not dir_exists(file):
            return await event.reply("__File or folder not found__")
        if dir_exists(file):
            ctrl = await event.reply(
                "Folder upload control panel.",
                buttons=[
                    [Button.inline("Cancel all", data="skip0")],
                ],
            )
            _id = f"{ctrl.chat_id}:{ctrl.id}"
            code(user=event.sender_id, index=_id)
            f_jump = event
            _no = 0
            for path, subdirs, files in os.walk(file):
                subdirs.sort()
                if not files:
                    if not os.listdir(path):
                        await event.reply(f"`📁 {path} is empty.`")
                    continue
                i = len(files)
                t = 1
                for name in sorted(files):
                    if _id in u_cancelled():
                        u_cancelled().remove(_id)
                        return await event.reply(u_can_msg)
                    file = os.path.join(path, name)
                    if size_of(file) > 2126000000:
                        chain_msg = await chain_msg.reply(
                            f"Uploading of `{name}` failed because file was larger than 2GB",
                            quote=True,
                        )
                        continue
                    while True and _id not in u_cancelled():
                        try:
                            cap = f"`{name}`"
                            ul = await chain_msg.reply(
                                f"**Uploading:-**\n`{name}`\n"
                                f"**from 📁:**\n `{path}`\n`({t}/{i})`…",
                                quote=True,
                            )
                            await asyncio.sleep(10)
                            upload = uploader()
                            d_msg = await upload.start(
                                event.chat_id,
                                file,
                                ul,
                                thumb,
                                cap,
                                chain_msg,
                            )
                            chain_msg = d_msg if d_msg else chain_msg
                            if not upload.is_cancelled:
                                await ul.delete()
                                _no = _no + 1
                            else:
                                await ul.edit(f"Uploading of `{name}` was cancelled.")
                                chain_msg = ul
                            t = t + 1
                        except pyro_errors.FloodWait as e:
                            await asyncio.sleep(e.value)
                            continue
                        except pyro_errors.BadRequest:
                            await asyncio.sleep(10)
                            continue
                        break
                    else:
                        u_cancelled().remove(_id)
                        return await event.reply(u_can_msg)
                await asyncio.sleep(10)
                f_jump = await f_jump.reply(
                    f"`All files in`:\n'`{path}`'\n`have been uploaded successfully. {enmoji()}`",
                )
                await asyncio.sleep(1)
            await ctrl.delete()

        else:
            _no = 1
            r = await message.reply(f"`Uploading {file}…`", quote=True)
            _none, cap = os.path.split(file)
            upload = uploader()
            await upload.start(event.chat_id, file, r, "thumb.jpg", f"`{cap}`", message)
            if not upload.is_cancelled:
                await r.edit(f"`{cap} uploaded successfully.`")
            else:
                await r.edit(f"`Uploading of {cap} has been cancelled.`")
        if uri:
            await asyncio.sleep(5)
            await event.reply(
                f"`{_no} file(s) have been uploaded from` `{args}` `successfully. {enmoji()}`"
            )
    except Exception:
        await logger(Exception)
    finally:
        if download and downloaded:
            rm_leech_file(download.uri_gid)
