import copy

from telethon import events

from bot import Button, asyncio, batch_lock, conf, errors, itertools, os, re, tele
from bot.config import _bot

from .ani_utils import qparse
from .bot_utils import (
    encode_job,
    get_bqueue,
    get_preview,
    get_queue,
    is_video_file,
    sdict,
)
from .db_utils import save2db
from .log_utils import log, logger
from .msg_utils import edit_message

STATUS_START = 0
PAGES = 1
PAGE_NO = 1
STATUS_LIMIT = 12
PARSE_STATUS = False


async def clean_batch(args=None, key=None):
    batch_queue = get_bqueue()
    if not (args or key):
        return
    if key:
        if batch_queue.get(key):
            async with batch_lock:
                batch_queue.pop(key)
        return
    args = int(args)
    queue = get_queue()
    if args > (len(queue) - 1):
        return
    _none, none_, vfm = list(queue.values())[args]
    if (vfm[2])[1].lower() != "batch.":
        return
    key = list(queue.keys())[args]
    await clean_batch(key=key)


async def get_preview_msg(file_list, batch_queue, ver=None, fil=None):
    msg = str()
    button = []
    cmd_s = conf.CMD_SUFFIX.strip()
    qn = sum(1 for st in batch_queue.values() if st == 1)
    try:
        i = len(batch_queue)
        globals()["PAGES"] = (i + STATUS_LIMIT - 1) // STATUS_LIMIT
        if PAGE_NO > PAGES and PAGES != 0:
            globals()["STATUS_START"] = (STATUS_LIMIT * PAGES) - 12
            globals()["PAGE_NO"] = PAGES

        for index_no, _no in zip(
            list(batch_queue.keys())[STATUS_START : STATUS_LIMIT + STATUS_START],
            itertools.count(STATUS_START),
        ):
            status = batch_queue.get(index_no)
            file_name = file_list[index_no]
            file_name = (os.path.split(file_name))[1]
            if PARSE_STATUS and status != 3:
                file_name = await qparse(file_name, ver=ver, fil=fil)

            msg += f"{_no}. `{file_name}`\n  └**Status:** `{sdict.get(status)}`\n\n"

        if not msg:
            return None, None
        if i > STATUS_LIMIT:
            # Create the Inline button
            btn_prev = Button.inline("<<", data="preview prev")
            btn_info = Button.inline(
                f"{PAGE_NO}/{PAGES} ({qn} of {i})", data="status 🙆"
            )
            btn_next = Button.inline(">>", data="preview next")
            # Define the button layout
            button.append([btn_prev, btn_info, btn_next])
        else:
            msg += f"**Pending Tasks:** {qn} of {i}\n"
        btn_cancel = Button.inline("Cancel", data="preview cancel")
        btn_done = Button.inline("Done", data="preview done")
        btn_parse = Button.inline(
            f"{'Parse' if not PARSE_STATUS else 'Raw'}", data="preview parse"
        )
        button.append([btn_parse, btn_done])
        button.append([btn_cancel])
        msg += f"\n**📌 Tip: To change the state of an item use** /select{cmd_s} <item number(s)>"

    except Exception:
        await logger(Exception)
        msg = "__An error occurred.__"
    return msg, button


async def preview_actions(event):
    try:
        data = event.pattern_match.group(1).decode().strip()
        global STATUS_START, PAGE_NO, PAGES, PARSE_STATUS
        async with batch_lock:
            if data == "next":
                if PAGE_NO == PAGES:
                    STATUS_START = 0
                    PAGE_NO = 1
                else:
                    STATUS_START += STATUS_LIMIT
                    PAGE_NO += 1
            elif data == "prev":
                if PAGE_NO == 1:
                    STATUS_START = STATUS_LIMIT * (PAGES - 1)
                    PAGE_NO = PAGES
                else:
                    STATUS_START -= STATUS_LIMIT
                    PAGE_NO -= 1
            elif data == "cancel":
                get_preview().clear()
                get_preview(list=True).clear()
                _bot.batch_ing.clear()
            elif data == "done":
                _bot.batch_ing.clear()
            elif data == "parse":
                PARSE_STATUS = not PARSE_STATUS

        await event.answer(f"{data}…")

    except Exception:
        await logger(Exception)


async def batch_preview(
    event, torrent, chat_id, e_id, v, f, reuse=False, user=None, select_all=False
):
    if _bot.batch_ing and not select_all:
        await event.reply("`Cannot edit two batches simultaneously.`")
        return
    user = user or event.sender_id
    _bot.batch_ing.append(user) if not select_all else None
    event2 = await event.reply("…")
    preview_queue = get_preview()
    preview_list = get_preview(list=True)
    result = None
    try:
        preview_list.extend(torrent.file_list)
        if not reuse:
            for file, no in zip(torrent.file_list, itertools.count()):
                state = 1 if select_all else None
                preview_queue.update({no: state if is_video_file(file) else 3})
        else:
            batch_db = get_bqueue().get((chat_id, e_id))
            if not batch_db:
                return
            preview_queue.update(batch_db[1])
        await asyncio.sleep(3)
        while True:
            if select_all:
                break
            if reuse and not get_queue().get((chat_id, e_id)):
                await edit_message(
                    event2, "`Batch no longer present in queue, exiting…`"
                )
                get_preview().clear()
                get_preview(list=True).clear()
                _bot.batch_ing.clear()
                return
            if not _bot.batch_ing:
                if not preview_queue:
                    return
                break
            async with batch_lock:
                msg, button = await get_preview_msg(
                    torrent.file_list, preview_queue, v, f
                )
            try:
                await event2.edit(msg, buttons=button)
                await asyncio.sleep(5)
            except errors.rpcerrorlist.MessageNotModifiedError:
                await asyncio.sleep(8)
                continue
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                continue
            except Exception:
                break

        pre_queue = copy.deepcopy(preview_queue)
        batch_queue = get_bqueue()
        batch_queue.update({(chat_id, e_id): [torrent, pre_queue]})
        result = 1
        await save2db("batches")
    except Exception:
        await logger(Exception)
    finally:
        preview_list.clear()
        preview_queue.clear()
        await event2.delete()
        return result


async def get_batch_list(
    exclude=None, limit=6, v=None, f=None, get_nleft=False, parse=True
):
    try:
        bqueue = get_bqueue()
        q_batch = list(bqueue.values())[0][1]
        q_list = list(bqueue.values())[0][0].file_list
        allwd_list = []
        rtn_list = []
        for k in list(q_batch.keys()):
            if q_batch.get(k) == 1:
                if (file_name := os.path.split(q_list[k])[1]) != exclude:
                    allwd_list.append(file_name)
        length = len(allwd_list)
        for name in allwd_list[:limit]:
            q = await qparse(name, ver=v, fil=f) if parse else name
            rtn_list.append(q)
        if get_nleft:
            nleft = (length - limit) if length > limit else None
            return rtn_list, nleft
        return rtn_list
    except Exception:
        log(Exception)


def get_downloadable_batch(q_id):
    bqueue = get_bqueue()
    file_name = k = name = None
    value = bqueue.get(q_id, False)
    if value is False:
        return None, None, None
    q_batch = value[1]
    q_list = value[0].file_list
    for k in list(q_batch.keys()):
        if q_batch.get(k) == 1:
            file_name, name = q_list[k], os.path.split(q_list[k])[1]
            break
    return file_name, k, name


def mark_file_as_done(file_id, q_id):
    if file_id is None:
        return
    if encode_job.pending():
        return
    bqueue = get_bqueue()
    value = bqueue.get(q_id, False)
    if value is False:
        return
    q_batch = value[1]
    q_batch.update({file_id: 2})


tele.add_event_handler(
    preview_actions, events.callbackquery.CallbackQuery(data=re.compile(b"preview(.*)"))
)
