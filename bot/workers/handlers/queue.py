from pyrogram.types import Message

from bot import asyncio, dl_pause, errors, itertools, queue_lock
from bot.fun.quips import enquip4
from bot.utils.ani_utils import qparse
from bot.utils.bot_utils import (
    bot_is_paused,
    get_f,
    get_filename,
    get_queue,
    get_v,
    get_var,
    is_magnet,
    is_url,
    pause,
    rm_pause,
    string_escape,
    video_mimetype,
)
from bot.utils.db_utils import save2db
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    get_args,
    msg_sleep_delete,
    try_delete,
    user_is_allowed,
    user_is_owner,
    valid_range,
)
from bot.utils.queue_utils import get_queue_msg, q_dup_check, queue_status
from bot.workers.downloaders.dl_helpers import get_leech_name


async def listqueue(event, args, client, deletable=True):
    """
    List items in queue in paged format
    with 10 items per page.

    Takes no argument.
    Not to be confused with /queue -p (different command)
    """
    if args:
        return
    if deletable:
        if not (user_is_allowed(event.sender_id) or not deletable):
            return await try_delete(event)
        if event.is_channel and not event.is_group:
            return
    queue = get_queue()
    empty_queue_msg = "`I'm as free as a bird 🦅`"
    lst_queue_msg = "`Listing queue pls wait…`"
    no_queued_msg = "`Nothing Here, yet! 💖`"
    if not queue:
        await msg_sleep_delete(event, empty_queue_msg)
        return await try_delete(event) if deletable else None
    if isinstance(event, Message):
        event2 = await client.send_message(
            event.chat.id,
            lst_queue_msg,
            reply_to=event.id,
        )
    else:
        event2 = await event.reply(lst_queue_msg)
    await queue_status(event2)
    await asyncio.sleep(2)

    while True:
        try:
            _is_duplicate = await q_dup_check(event2)
            if _is_duplicate:
                await event2.delete()
                break
            async with queue_lock:
                msg, button = await get_queue_msg()
            if not msg:
                await msg_sleep_delete(event2, no_queued_msg, edit=True)
                break
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
    if deletable:
        await try_delete(event)
    return


async def listqueuep(event, args, client):
    """
    Send a range of number or number of item in queue to be parsed.\nrange maximum 10.
    if using range first and last number must be within the limits of the number of items on queue and must be less than or equal to 10.
    for instance /queue -p 1-10 to print the parsed list of all queued items indexed 1-10.
    pass 0 as number to get currently encoding.
    """
    async with event.client.action(event.chat_id, "typing"):
        if not user_is_allowed(event.sender_id):
            return await try_delete(event)
        queue = get_queue()
        empty_queue_msg = "`Nothing In Queue`"
        if not queue:
            await msg_sleep_delete(event, empty_queue_msg, time=3)
            return await try_delete(event)
        try:
            if args.isdigit() and ((args := int(args)) <= (len(queue) - 1)):
                file = list(queue.values())[args]
                # Backwards compatibility:
                v, f = file[2] if isinstance(file[2], tuple) else (file[2], None)
                p_file_name = await qparse(file[0], v, f)
                return await event.reply(str(args) + ". `" + p_file_name + "`")

            if not valid_range(args):
                return await event.reply(
                    "Send a range of number or number of item in queue to be parsed.\n**Range:** `1-10` Maximum 10."
                )
            x, y = map(int, args.split("-"))
            if (y - x) > 10 or y == x or x > (len(queue) - 1) or y > (len(queue) - 1):
                return await event.reply(
                    "First and last number must be within the limits of the number of items on queue and must be less than or equal to 10."
                )
            rply = str()
            y = y + 1
            for file, i in zip(list(queue.values())[x:y], itertools.count(start=1)):
                # Backwards compatibility:
                v, f = file[2] if isinstance(file[2], tuple) else (file[2], None)
                file_name = await qparse(file[0], v, f)
                rply += f"{i}. `{file_name}`\n\n"
            if rply:
                rply += "\n**Queue based on auto-generated filename if you you want the actual queue use the command** /queue"

        except Exception:
            rply = "__An error occurred.__"
            await logger(Exception)
        return await event.reply(rply)


async def enleech(event, args, client):
    """
    Adds a link or torrent link to encoding queue:
        Requires a reply to link or the link as argument
        can also add consecutive items to queue by replying
        to the first link and a number of how many links to add to queue
    Accepts the following flags:
        -f filter (only use if familiar with filter format)
        -rm what_to_remove (keyword to remove from torrent file_name)
        -tc caption_tag (tag caption type as…)
        -tf file_tag (tag file_as)
        -v number (tag according to version number)
    Both flags override /filter & /v

    :: filter format-
        what_to_remove\\ntag_file_as\\ntag_caption_as
    ::
    """
    chat_id = event.chat_id
    user_id = event.sender_id
    if not user_is_allowed(user_id):
        return
    cust_fil = cust_v = str()
    queue = get_queue()
    invalid_msg = "`Invalid torrent/direct link`"
    no_uri_msg = (
        "`uhm you need to reply to or send command alongside a uri/direct link`"
    )
    no_dl_spt_msg = "`File to download is…\neither not a video\nor is a batch torrent which is currently not supported.`"
    str_esc = string_escape
    ukn_err_msg = "`An unknown error occurred, might an internal issue with aria2.\nCheck logs for more info`"
    if args:
        flag, args = get_args(
            "-f", "-rm", "-tc", "-tf", "-v", to_parse=args, get_unknown=True
        )
        if flag.rm or flag.tc or flag.tf:
            cust_fil = flag.rm or "disabled__"
            cust_fil += str().join(
                f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
            )
        else:
            cust_fil = str_esc(flag.f)
        cust_v = flag.v
    try:
        if event.is_reply:
            rep_event = await event.get_reply_message()
            if rep_event.media:
                await event.reply("**Warning:** `Use /add for files instead.`")
                return await addqueue(event, args, client)
            if args:
                if not args.isdigit():
                    return await event.reply(
                        f"**Yeah No.**\n`Error: expected a number but received '{args}'.`"
                    )
                args = int(args)
                async with queue_lock:
                    for _none, _id in zip(
                        range(args), itertools.count(start=rep_event.id)
                    ):
                        event2 = await client.get_messages(event.chat_id, _id)
                        if event2.empty:
                            await event.reply(
                                f"Resend uri links and try replying the first with /l or /leech again"
                            )
                            return await rm_pause(dl_pause, 5)
                        uri = event2.text
                        if not uri:
                            return await event.reply(no_uri_msg)
                        if not (is_url(uri) or is_magnet(uri)):
                            await event2.reply(invalid_msg)
                            return await rm_pause(dl_pause, 5)
                        file_name = await get_leech_name(uri)
                        if file_name is None or file_name.startswith("aria2_error"):
                            error = (
                                file_name.split("aria2_error")[1].strip()
                                if file_name
                                else file_name
                            )
                            await event2.reply(
                                ukn_err_msg, quote=True
                            ) if not error else await event2.reply(
                                f"`{error}`", quote=True
                            )
                            await asyncio.sleep(10)
                            continue
                        if not file_name:
                            await event2.reply(no_dl_spt_msg, quote=True)
                            await asyncio.sleep(5)
                            continue
                        already_in_queue = False
                        for item in queue.values():
                            if file_name in item:
                                await event2.reply(
                                    "**THIS LINK HAS ALREADY BEEN ADDED TO QUEUE**",
                                    quote=True,
                                )
                                await asyncio.sleep(5)
                                already_in_queue = True
                                break
                        if already_in_queue:
                            continue
                        if not bot_is_paused():
                            pause(status=dl_pause)

                        queue.update(
                            {
                                (chat_id, event2.id): [
                                    file_name,
                                    (user_id, event2),
                                    (cust_v or get_v(), cust_fil or get_f()),
                                ]
                            }
                        )
                        await save2db()

                        msg = await event2.reply(
                            f"**Link added to queue ⏰, POS:** `{len(queue)-1}`\n`Please Wait , Encode will start soon`",
                            quote=True,
                        )
                        if len(queue) > 1:
                            asyncio.create_task(
                                listqueue(msg, None, event.client, False)
                            )
                        await asyncio.sleep(5)
                    return await rm_pause(dl_pause)
            else:
                uri = rep_event.text
                event = rep_event
        else:
            uri = args

        if not uri:
            return await event.reply(no_uri_msg)
        if not (is_url(uri) or is_magnet(uri)):
            return await event.reply(invalid_msg)
        file_name = await get_leech_name(uri)
        if file_name is None or (file_name and file_name.startswith("aria2_error")):
            error = (
                file_name.split("aria2_error")[1].strip() if file_name else file_name
            )
            return (
                await event.reply(ukn_err_msg)
                if not error
                else await event.reply(f"`{error}`")
            )
        if not file_name:
            return await event.reply(no_dl_spt_msg)
        for item in queue.values():
            if file_name in item:
                return await event.reply(
                    "**THIS TORRENT HAS ALREADY BEEN ADDED TO QUEUE**"
                )
        queue.update(
            {
                (chat_id, event.id): [
                    file_name,
                    (user_id, None),
                    (cust_v or get_v(), cust_fil or get_f()),
                ]
            }
        )
        await save2db()
        if len(queue) > 1 or bot_is_paused():
            msg = await event.reply(
                f"**Torrent added To Queue ⏰, POS:** `{len(queue)-1}`\n`Please Wait , Encode will start soon`"
            )
            if len(queue) > 1:
                return asyncio.create_task(listqueue(msg, None, event.client, False))
    except Exception:
        await logger(Exception)
        await rm_pause(dl_pause)
        return await event.reply("An Unknown error Occurred.")


async def pencode(message, args=None, sender_id=None, flag=None):
    try:
        if not (message.from_user or sender_id):
            return await msg_sleep_delete(message, f"`{enquip4()}`", time=20)
        chat_id = message.chat.id
        sender_id = sender_id or message.from_user.id
        if sender_id != chat_id and not get_var("groupenc"):
            return await msg_sleep_delete(
                message,
                "**Pm me with files to encode instead\nOR\nSend** `/groupenc on` **to turn on group encoding!**\n__This message will self destruct in 10 seconds__",
            )
        if not (user_is_allowed(chat_id) or user_is_allowed(sender_id)):
            return await message.delete()
        if message.document:
            if message.document.mime_type not in video_mimetype:
                return
        if get_queue() or bot_is_paused():
            xxx = await message.reply("`Adding To Queue`", quote=True)
        name = get_filename(message)
        queue = get_queue()
        for item in queue.values():
            if name in item:
                return await xxx.edit("**THIS FILE HAS ALREADY BEEN ADDED TO QUEUE**")
        cust_fil = cust_v = str()
        if args:
            if not flag:
                flag, args = get_args(
                    "-f", "-rm", "-tc", "-tf", "-v", to_parse=args, get_unknown=True
                )
            if flag.rm or flag.tc or flag.tf:
                cust_fil = flag.rm or "disabled__"
                cust_fil += str().join(
                    f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
                )
            else:
                cust_fil = str_esc(flag.f)
            cust_v = flag.v
        queue.update(
            {
                (chat_id, message.id): [
                    name,
                    (sender_id, message),
                    (cust_v or get_v(), cust_fil or get_f()),
                ]
            }
        )
        await save2db()
        if len(queue) > 1 or bot_is_paused():
            await xxx.edit(
                f"**Added To Queue ⏰, POS:** `{len(queue)-1}` \n`Please Wait , Encode will start soon`"
            )
        await add_multi(message, args, sender_id, flag)
        return
    except BaseException:
        await logger(BaseException)


async def add_multi(message, args, sender_id, flag):
    if args and args.isdigit():
        args = int(args) - 1
        if args < 1:
            return
        else:
            args = str(args)
        media = await message._client.get_messages(chat_id, message.id + 1)
        if media.empty:
            return
        asyncio.create_task(pencode(media, args, sender_id, flag))
        return


async def addqueue(event, args, client):
    """
    Add replied video to queue with args
    Accepts the same argument as /l
    can also be used to reuse a leech command
    """
    user_id = event.sender_id
    if not user_is_allowed(user_id):
        return
    if not event.is_reply:
        return event.reply("Command needs to be a replied message.")
    try:
        event_2 = await event.get_reply_message()
        if event_2.media:
            media = await client.get_messages(event.chat_id, event2.id)
            if media.empty:
                return await event.reply("Try again!")
            await pencode(media, args, user_id)
            return
        if event_2.text.startswith("/l"):
            args = (
                event.text.split(split_args, maxsplit=1)[1].strip()
                if len(event.text.split()) > 1
                else None
            )
            await enleech(event_2, args, client)
            return
        await event.reply(addqueue.__doc__)
    except Exception:
        logger(Exception)
    finally:
        await try_delete(event)


async def clearqueue(event, args, client):
    """
    Clears an item or all items from queue
    Now requires an argument to prevent accidents.
        - pass a number or a range of numbers representing a queue item or queue items to remove __(check with queue)__
        - pass 'all' (not case sensitive) remove all 'pending' queue items
    """
    user = event.sender_id
    if not user_is_allowed(user):
        return await event.delete()

    btch_clr_msg = "**Cleared the following files from queue:**\n"
    queue = get_queue()

    if not queue or len(queue) == 1:
        return await event.reply("`No Queued items.`")
    if args.isdigit():
        i = int(args)
        queue = get_queue()
        if i > (len(queue) - 1):
            return await event.reply("Enter a valid queue number")
        adder = (list(queue.values())[i])[1]
        if not user_is_owner(user) and user != adder[0]:
            return await event.reply(
                "You didn't add this to queue so you can't remove it!"
            )
        q_values = list(queue.values())[i]
        async with queue_lock:
            queue.pop(list(queue.keys())[i])
        await event.reply(f"`{q_values[0]}` has been removed from queue")
        return await save2db()
    if "-" in args and not valid_range(args):
        return await event.reply("Send a valid range of numbers")
    elif "-" in args:
        x, y = map(int, args.split("-"))
        if x > (len(queue) - 1) or y > (len(queue) - 1):
            return await event.reply("Given range is more than total items on queue ")
        y = y + 1
        reply = str()
        for key, i in zip(list(queue.keys())[x:y], itertools.count(start=1)):
            adder = (queue.get(key)[1])[0]
            if not user_is_owner(user) and user != adder:
                continue
            reply += "{0}. `{1}`\n".format(i, queue.get(key)[0])
            async with queue_lock:
                queue.pop(key)
        if not reply:
            return await event.reply("`Nothing was cleared.`")
        msg = await event.reply(btch_clr_msg + reply)
    elif args.casefold() == "all":
        reply = str()
        for key, i in zip(list(queue.keys())[1:], itertools.count(start=1)):
            adder = (queue.get(key)[1])[0]
            if not user_is_owner(user) and user != adder:
                continue
            reply += "{0}. `{1}`\n".format(i, queue.get(key)[0])
            async with queue_lock:
                queue.pop(key)
        if not reply:
            return await event.reply("`Nothing was cleared.`")
        msg = await event.reply(btch_clr_msg + reply)
    elif not args.isdigit():
        return await event.reply(
            "`Pass a number/range/all for an item/items on queue to be removed.`"
        )

    await save2db()
    await asyncio.sleep(7)
    await try_delete(event)
    await msg.delete()
    return
