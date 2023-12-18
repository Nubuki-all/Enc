import asyncio
import shutil
from os.path import split as path_split

from bot import Path, pyro, pyro_errors
from bot.config import conf
from bot.utils.log_utils import logger
from bot.utils.os_utils import parse_dl, s_remove
from bot.workers.uploaders.upload import Uploader as uploader

h_sticker = "CAACAgEAAxkBAAI0aWKx36P2GY9Fq6xvN0SBU1V2xZYIAAKXAgACJ_hhR9HcWzoditT7HgQ"


async def dumpdl(dl, name, thum, user, message):
    dmp = "dump/" + (path_split(dl))[1]
    try:
        shutil.copy2(dl, dmp)
        _dmp = Path(dmp)
        dump_ = conf.DUMP_CHANNEL or None
        fname = f"`{name}`"
        sticker = conf.FSTICKER or h_sticker
        if dump_:
            message = await pyro.send_message(
                dump_, "`🚨 Incoming! 🚨`\n\n" + await parse_dl(name)
            )
            await asyncio.sleep(5)
            reply = await message.reply(f"__Dumping:__\n {fname}__…__", quote=True)
            user = dump_
        elif message:
            reply = await message.reply(f"`Dumping` {fname}`…`", quote=True)
        await asyncio.sleep(2)
        if int(_dmp.stat().st_size) > 2126000000:
            dp = await reply.reply("**File too large to dump, Aborting…**", quote=True)
            f_reply = reply
        else:
            u_id = f"{reply.chat.id}:{reply.id}"
            upload = uploader(_id=u_id)
            dp = await upload.start(user, dmp, reply, thum, fname, message)

            if not upload.is_cancelled:
                f_reply = await reply.edit(f"{fname} __dumped successfully.__")
            else:
                f_reply = await reply.edit(f"`Dumping of {fname} was cancelled.`")
        if conf.LOG_CHANNEL:
            chat = int(conf.LOG_CHANNEL)
            await f_reply.copy(chat_id=chat)
            if dp is not None:
                await dp.copy(chat_id=chat)
    except pyro_errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await dumpdl(dl, name, thum, user, message)
    except pyro_errors.BadRequest:
        await asyncio.sleep(20)
        await dumpdl(dl, name, thum, user, message)
    except Exception:
        await logger(Exception)
    finally:
        s_remove(dmp)
        await asyncio.sleep(5)
        if dump_:
            await message.reply_sticker(sticker, quote=False)
