from bot import FCHANNEL as forward
from bot import FCHANNEL_STAT as forward_id
from bot import asyncio, glob, itertools, os, pyro, startup_, tele
from bot.fun.emojis import enmoji
from bot.fun.quips import enquip4
from bot.fun.quotes import enquotes
from bot.utils.ani_utils import qparse
from bot.utils.bot_utils import QUEUE as queue
from bot.utils.bot_utils import get_codec, get_pause_status


async def encodestat():
    if not queue:
        msg = "**Currently Resting…😑**"
        return msg
    msg = str()
    try:
        try:
            # depreciating this method...
            dt_ = glob.glob("encode/*")
            data = max(dt_, key=os.path.getctime)
            file_name = data.replace("encode/", "")
        except Exception:
            out = list(queue.values())[0]
            #Backwards compatibility:
            v, f = out[2] if isinstance(out[2], tuple) else out[2], None
            file_name = await qparse(out[0], v, f)
        s = "🟢" if get_pause_status() != 0 else "⏸️"
        msg = (
            f"{s} `{file_name}`\n\n"
            "    **CURRRENT ITEMS ON QUEUE:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        for key, i in zip(list(queue.keys())[1:], itertools.count(start=1)):
            if i > 6:
                r = len(queue) - i
                msg += f"__+{r} more…__\n"
                break
            out = queue.get(key)
            #Backwards compatibility:
            v, f = out[2] if isinstance(out[2], tuple) else out[2], None
            name = await qparse(out[0], v, f)
            msg += f"{i}. `{name}`\n"

        if len(queue) == 1:
            loc = await enquotes()
            msg += f"Nothing Here; While you wait:\n\n{loc}"
    except Exception:
        pass
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
        while forward_id:
            if not queue:
                if check:
                    await asyncio.sleep(60)
                    continue
                check.append(1)

            else:
                check.clear() if check else None
            if startup_:
                estat = await encodestat()
            else:
                estat = f"**{enquip4()} {enmoji()}**"
            await stateditor(estat, forward, forward_id)
            await asyncio.sleep(60)
