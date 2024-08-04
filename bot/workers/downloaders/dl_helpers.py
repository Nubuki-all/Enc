import uuid

from bot import asyncio, math, os, pyro, qbClient, time
from bot.config import _bot, conf
from bot.utils.bot_utils import (
    Qbit_c,
    get_aria2,
    get_queue,
    replace_proxy,
    sync_to_async,
)
from bot.utils.log_utils import log, logger


def clean_aria_dl(download):
    aria2 = get_aria2()
    download.remove(force=True, files=True)
    if download.following_id:
        download = aria2.get_download(download.following_id)
        download.remove(force=True, files=True)


def rm_leech_file(*gids):
    for gid in gids:
        try:
            if not gid:
                break
            aria2 = get_aria2()
            download = aria2.get_download(gid)
            download.remove(force=True, files=True)
            if download.followed_by_ids:
                download = aria2.get_download(download.followed_by_ids[0])
                download.remove(force=True, files=True)
        except Exception:
            log(Exception)


def get_qbclient():
    return qbClient(
        host="localhost",
        port=conf.QBIT_PORT,
        VERIFY_WEBUI_CERTIFICATE=False,
        REQUESTS_ARGS={"timeout": (30, 60)},
    )


async def rm_torrent_file(*hashes, qb=None):
    if not qb:
        qb = await sync_to_async(get_qbclient)
    for hash in hashes:
        try:
            await sync_to_async(
                qb.torrents_delete, delete_files=True, torrent_hashes=hash
            )
        except Exception:
            log(Exception)


async def rm_torrent_tag(*tags, qb=None):
    if not qb:
        qb = await sync_to_async(get_qbclient)
    for tag in tags:
        try:
            await sync_to_async(qb.torrents_delete_tags, tags=tag)
        except Exception:
            log(Exception)


async def get_files_from_torrent(hash, tag=None):
    # qb.login()
    qb = await sync_to_async(get_qbclient)
    torrent = await sync_to_async(qb.torrents_info, torrent_hash=hash, tag=tag)
    files = torrent[0].files
    file_list = [file["name"] for file in files]
    return file_list


async def download2(dl, file, message=None, e=None):
    try:
        if not message:
            return asyncio.create_task(
                pyro.download_media(
                    message=file,
                    file_name=dl,
                )
            )
        ttt = time.time()
        media_type = str(message.media)
        if media_type == "MessageMediaType.DOCUMENT":
            media_mssg = "`Downloading a file…`\n"
        else:
            media_mssg = "`Downloading a video…`\n"
        download_task = asyncio.create_task(
            pyro.download_media(
                message=message,
                file_name=dl,
                progress=progress_for_pyrogram,
                progress_args=(pyro, media_mssg, e, ttt),
            )
        )
        return download_task
    except Exception:
        await logger(Exception)


async def get_leech_name(url):
    aria2 = get_aria2()
    dinfo = Qbit_c()
    try:
        url = replace_proxy(url)
        downloads = await sync_to_async(aria2.add, url, {"dir": f"{os.getcwd()}/temp"})
        c_time = time.time()
        while True:
            download = await sync_to_async(aria2.get_download, downloads[0].gid)
            download = download.live
            if download.followed_by_ids:
                gid = download.followed_by_ids[0]
                download = await sync_to_async(aria2.get_download, gid)
            if time.time() - c_time > 300:
                dinfo.error = "E408: Getting filename timed out."
                break
            if download.status == "error":
                dinfo.error = "E" + download.error_code + ": " + download.error_message
                break
            if download.name.startswith("[METADATA]") or download.name.endswith(
                ".torrent"
            ):
                await asyncio.sleep(2)
                continue
            if not (os.path.splitext(download.name))[1] and not download.total_length:
                await asyncio.sleep(2)
                continue

            dinfo.name = download.name
            break
        await sync_to_async(clean_aria_dl, download)
    except Exception as e:
        dinfo.error = e
        await logger(Exception)
    finally:
        return dinfo


async def get_torrent(url):
    qinfo = Qbit_c()
    tag = "qb_dl" + str(uuid.uuid4())
    url = replace_proxy(url)
    try:
        qb = await sync_to_async(get_qbclient)
        op = await sync_to_async(
            qb.torrents_add,
            url,
            save_path=os.getcwd() + "/temp",
            seeding_time_limit=0,
            is_paused=False,
            tags=tag,
        )
        st = time.time()
        if op.lower() == "ok.":
            tor_info = await sync_to_async(qb.torrents_info, tag=tag)
            if len(tor_info) == 0:
                while True:
                    tor_info = await sync_to_async(qb.torrents_info, tag=tag)
                    if len(tor_info) > 0:
                        break
                    elif time.time() - st >= conf.QBIT_TIMEOUT:
                        qinfo.error = "Failed to add torrent…"
                        return
        else:
            qinfo.error = "This Torrent already added or unsupported/invalid link/file"
            return
        if tor_info[0].state == "metaDL":
            st = time.time()
            while True:
                tor_info = await sync_to_async(qb.torrents.info, tag=tag)
                if tor_info[0].state != "metaDL":
                    break
                elif time.time() - st >= 360:
                    qinfo.error = "Failed to get metadata…"
                    return
        if tor_info[0].state == "error":
            qinfo.error = "An unknown error occurred."
            return
        qinfo.hash = tor_info[0].hash
        await sync_to_async(qb.torrents_pause, torrent_hashes=qinfo.hash)
        qinfo.file_list = await get_files_from_torrent(qinfo.hash, tag)
        qinfo.count = len(qinfo.file_list)
        name = (os.path.split(qinfo.file_list[0]))[1] if qinfo.count == 1 else None
        qinfo.name = name or tor_info[0].name
        await rm_torrent_file(qinfo.hash, qb=qb)
        await rm_torrent_tag(tag, qb=qb)
        return
    except Exception as e:
        qinfo.error = e
        await logger(Exception)
    finally:
        return qinfo


async def cache_dl(check=False):
    if check:
        return _bot.cached
    try:
        queue = get_queue()
        chat_id, msg_id = list(queue.keys())[1]
        filename, u_msg, v = list(queue.values())[1]
        dl = "downloads/" + filename
        user, msg = u_msg
        if not msg:
            msg = await pyro.get_messages(chat_id, msg_id)
        else:
            msg._client = pyro
        if msg.text:
            return
        media_type = str(msg.media)
        if media_type == "MessageMediaType.VIDEO":
            file = msg.video.file_id
        else:
            file = msg.document.file_id
        await download2(dl, file)
        _bot.cached = True
    except Exception:
        await logger(Exception)
        _bot.cached = False


async def progress_for_pyrogram(current, total, bot, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        status = "downloads" + "/status.json"
        if os.path.exists(status):
            with open(status, "r+") as f:
                statusMsg = json.load(f)
                if not statusMsg["running"]:
                    bot.stop_transmission()
        speed = current / diff
        time_to_completion = time_formatter(int((total - current) / speed))
        progress = "{0}{1} \n<b>Progress:</b> {2}%\n".format(
            "".join(
                [conf.FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]
            ),
            "".join(
                [
                    conf.UN_FINISHED_PROGRESS_STR
                    for i in range(10 - math.floor(percentage / 10))
                ]
            ),
            round(percentage, 2),
        )

        tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
            hbs(current),
            hbs(total),
            hbs(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            time_to_completion if time_to_completion else "0 s",
        )
        try:
            if not message.photo:
                await message.edit_text(text="{}\n {}".format(ud_type, tmp))
            else:
                await message.edit_caption(caption="{}\n {}".format(ud_type, tmp))
        except BaseException:
            pass
