import uuid

from bot import asyncio, math, os, pyro, time
from bot.config import _bot, conf
from bot.utils.bot_utils import (
    get_queue,
    replace_proxy,
    sync_to_async,
)
from bot.utils.log_utils import log, logger



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
