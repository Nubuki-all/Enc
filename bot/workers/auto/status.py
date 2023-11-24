from bot import FCHANNEL as forward
from bot import FCHANNEL_STAT as forward_id
from bot import asyncio, itertools, pyro, startup_, tele
from bot.fun.emojis import enmoji
from bot.fun.quips import enquip4
from bot.fun.quotes import enquotes
from bot.fun.stuff import lvbar
from bot.utils.ani_utils import qparse
from bot.utils.batch_utils import get_batch_list
from bot.utils.bot_utils import QUEUE as queue
from bot.utils.bot_utils import BATCH_QUEUE as bqueue
from bot.utils.bot_utils import encode_info, get_codec, get_pause_status
from bot.utils.log_utils import logger


async def batch_status_preview(msg, v, f):
    msg += "  **CURRENTLY QUEUED ITEMS IN BATCH:**\n" f"{lvbar}\n"
    blist, left = await get_batch_list(encode_info._current, v=v, f=f, get_nleft=True)
    for name, i in zip(blist, itertools.count(start=1)):
        msg += f"{i}. `{name}`\n"
    if left:
        msg += f"__+{left} more…__\n"
    if not blist:
        loc = await enquotes()
        msg += f"Nothing Here; While you wait:\n\n{loc}\n"
    return msg


async def queue_status_preview(start, msg, queue):
    msg += "    **CURRRENT ITEMS ON QUEUE:**\n" f"{lvbar}\n"
    for key, i in zip(list(queue.keys())[start:], itertools.count(start=1)):
        if i > 6:
            r = len(queue) - i if start else (len(queue) + 1) - i
            msg += f"__+{r} more…__\n"
            break
        out = queue.get(key)
        v, f, m = out[2]
        name = (
            await qparse(out[0], v, f)
            if m[1].lower() != "batch."
            else f"[Batch]:- {out[0]}"
        )
        msg += f"{i}. `{name}`\n"
    return msg


async def encodestat():
    if not queue:
        msg = "**Currently Resting…😑**"
        return msg
    single = True
    msg = str()
    try:
        i = 0
        msg = str()
        s = "Currently Encoding:" if get_pause_status() != 0 else "Paused:"
        if file_name := encode_info.current:
            i = 1
            msg += f"```{s}\n{file_name}```\n\n"
        key = list(queue.keys())[0]
        out = queue.get(key)
        v, f, m = out[2]
        if m[1].lower() == "batch.":
            msg = await batch_status_preview(msg, v, f)
            single = False
        else:
            msg = await queue_status_preview(i, msg, queue)
        if len(queue) == 1 and single:
            loc = await enquotes()
            msg += f"Nothing Here; While you wait:\n\n{loc}"
        elif not single and (r := (len(queue) - 1)):
            msg += f"\n__(+{r} more item(s) on queue.)__ \n"
    except Exception:
        # pass
        await logger(Exception)
    me = await tele.get_me()
    codec = await get_codec()
    msg += f"\n\nYours truly,\n  {enmoji()} `{me.first_name}`"
    msg += f"\n    == {codec} =="
    return msg


async def stateditor(x, channel, id):
    try:
        return await pyro.edit_message_text(channel, id, x)

    except Exception:
        pass


async def autostat():
    if forward and forward_id:
        check = []
        check_queue = {}
        check_batch = {}
        def wait():
            if queue == check_queue and bqueue == check_batch:
                return True
            check_queue.clear(), check_queue.update(queue)
            check_batch.clear(), check_batch.update(bqueue)
            return False
        while forward_id:
            if not queue:
                if check:
                    await asyncio.sleep(60)
                    continue
                check.append(1)

            else:
                check.clear() if check else None
            if startup_:
                if not wait():
                    estat = await encodestat()
            else:
                estat = f"**{enquip4()} {enmoji()}**"
            await stateditor(estat, forward, forward_id)
            await asyncio.sleep(60)
