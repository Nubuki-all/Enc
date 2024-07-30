from pyrogram.types import Message

from bot import asyncio, dl_pause, errors, itertools, queue_lock
from bot.fun.quips import enquip4
from bot.utils.ani_utils import qparse
from bot.utils.batch_utils import batch_preview, clean_batch
from bot.utils.bot_utils import (
    bot_is_paused,
    check_cmds,
    get_bqueue,
    get_f,
    get_filename,
    get_pause_status,
    get_preview,
    get_previewer,
    get_queue,
    get_v,
    get_var,
    is_magnet,
    is_url,
    is_video_file,
    pause,
    rm_pause,
    sdict,
    split_text,
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
from bot.workers.downloaders.dl_helpers import get_leech_name, get_torrent

str_esc = string_escape


async def listqueue(event, args, client, deletable=True):
    """
    List items in queue in paged format
    with 10 items per page.

    Argument:
     -e (to edit configurations for queued items)
     -p (for parsed queue)
       Not live (Doesn't reflect changes to actual queue)
       for additional help send without additional arguments
    """
    if args:
        or_args = args
        flag, args = get_args(
            ["-e", "store_true"], ["-p", "store_true"], to_parse=args, get_unknown=True
        )
        if flag.e:
            if not args:
                return await event.reply(f"`{edit_queue.__doc__}`")
            return await edit_queue(event, or_args, client)
        if flag.p:
            if not args:
                return await event.reply(f"`{listqueuep.__doc__}`")
            return await listqueuep(event, or_args, client)
        return await event.reply(f"Unknown args: {args}")
    if deletable:
        if not user_is_allowed(event.sender_id):
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
        flag, args = get_args(["-p", "store_true"], to_parse=args, get_unknown=True)
        try:
            if args.isdigit() and ((args := int(args)) <= (len(queue) - 1)):
                file = list(queue.values())[args]
                v, f, m, n, au = file[2]
                p_file_name = (
                    await qparse(file[0], v, f, n, au[0])
                    if not m[1].lower() == "batch."
                    else "[Batch]: " + file[0]
                )
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
                v, f, m, n, au = file[2]
                file_name = (
                    await qparse(file[0], v, f, n, au[0])
                    if not m[1].lower() == "batch."
                    else "[Batch]: " + file[0]
                )
                rply += f"{i}. `{file_name}`\n\n"
            if rply:
                rply += "\n**Queue based on auto-generated filename if you you want the actual queue use the command** /queue"

        except Exception:
            rply = "__An error occurred.__"
            await logger(Exception)
        return await event.reply(rply)


async def enleech(event, args: str, client, direct=False):
    """
    Adds a link or torrent link to encoding queue:
        Requires a reply to link or the link as argument
        can also add consecutive items to queue by replying
        to the first link and a number of how many links to add to queue
    Accepts the following flags:
        -da Disables anilist for the item
        -f filter (only use if familiar with filter format)
        -rm what_to_remove (keyword to remove from torrent file_name)
        -n new_filename.mp4 (rename the processed file.)
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
    if not (user_is_allowed(user_id) or direct):
        return
    anilist = True
    cust_fil = cust_v = str()
    force_name = None
    mode = "None"
    o_args = None
    queue = get_queue()
    invalid_msg = "`Invalid torrent/direct link`"
    no_uri_msg = (
        "`uhm you need to reply to or send command alongside a uri/direct link`"
    )
    no_dl_spt_msg = "`File to download is…\neither not a video\nor is a batch torrent which is currently not supported.`"
    ukn_err_msg = "`An unknown error occurred, might an internal issue with aria2.\nCheck logs for more info`"
    if args:
        o_args = args
        flag, args = get_args(
            "-f",
            "-rm",
            "-n",
            "-tc",
            "-tf",
            "-v",
            ["-da", "store_false"],
            to_parse=args,
            get_unknown=True,
        )
        if flag.rm or flag.tc or flag.tf:
            cust_fil = flag.rm or "disabled__"
            cust_fil += str().join(
                f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
            )
        else:
            cust_fil = str_esc(flag.f)
        anilist = flag.da
        cust_v = flag.v
        force_name = flag.n
    try:
        if event.is_reply:
            rep_event = await event.get_reply_message()
            if rep_event.file:
                await event.reply("**Warning:** `Use /add for files instead.`")
                return await addqueue(event, o_args, client)
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
                        file = await get_leech_name(uri)
                        if file.error:
                            await event2.reply(f"`{file.error}`", quote=True)
                            await asyncio.sleep(10)
                            continue
                        if not is_video_file(file.name):
                            await event2.reply(no_dl_spt_msg, quote=True)
                            await asyncio.sleep(5)
                            continue
                        already_in_queue = False
                        for item in queue.values():
                            if file.name in item:
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
                                    file.name,
                                    (user_id, event2),
                                    (
                                        cust_v or get_v(),
                                        cust_fil or get_f(),
                                        ("aria2", mode),
                                        force_name,
                                        (anilist, uri),
                                    ),
                                ]
                            }
                        )
                        await save2db()

                        msg = await event2.reply(
                            f"**Link added to queue ⏰, POS:** `{len(queue)-1}`\n`Please Wait , Encode will start soon`",
                            quote=True,
                        )
                        await asyncio.sleep(5)
                    if len(queue) > 1:
                        asyncio.create_task(listqueue(msg, None, event.client, False))
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
        file = await get_leech_name(uri)
        if file.error:
            return await event.reply(f"`{file.error}`")
        if not is_video_file(file.name):
            return await event.reply(no_dl_spt_msg)
        for item in queue.values():
            if file.name in item:
                return await event.reply(
                    "**THIS TORRENT HAS ALREADY BEEN ADDED TO QUEUE**"
                )
        async with queue_lock:
            queue.update(
                {
                    (chat_id, event.id): [
                        file.name,
                        (user_id, None),
                        (
                            cust_v or get_v(),
                            cust_fil or get_f(),
                            ("aria2", mode),
                            force_name,
                            (anilist, uri),
                        ),
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
    except Exception as e:
        await logger(Exception)
        await rm_pause(dl_pause)
        return await event.reply(f"An error Occurred:\n - {e}")


async def enleech2(event, args: str, client, direct=False):
    """
    Adds a torrent link to encoding queue using qbittorrent:
        Requires a reply to link or the link as argument
        can also add consecutive items to queue by replying
        to the first link and a number of how many links to add to queue
        (doesn't work if -b is specified)
    Accepts the following flags:
        -b (To force encode batch)
        -d set name for batch or selected file in batch (useful to avoid duplication)
        -da Disables anilist for the item
        -y (in conjunction with -b) add all batch to queue without preview
        -f filter (only use if familiar with filter format)
        -rm what_to_remove (keyword to remove from torrent file_name)
        -n new_filename.mp4 (rename the processed file.)
        -s (select a file for encoding __ through indexing)
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
    if not (user_is_allowed(user_id) or direct):
        return
    anilist = True
    cust_fil = cust_v = flag = str()
    force_name = None
    queue = get_queue()
    invalid_msg = "`Invalid torrent/direct link`"
    mode = "None"
    no_uri_msg = (
        "`uhm you need to reply to or send command alongside a uri/direct link`"
    )
    no_bt_spt_msg = "`Torrent is a batch torrent.\nTo add to queue use -b`"
    no_fl_spt_msg = "`File is not a video.`"
    or_event = event
    if args:
        flag, args = get_args(
            "-d",
            "-f",
            "-rm",
            "-n",
            "-s",
            "-tc",
            "-tf",
            "-v",
            ["-b", "store_true"],
            ["-da", "store_false"],
            ["-y", "store_true"],
            to_parse=args,
            get_unknown=True,
        )
        if flag.rm or flag.tc or flag.tf:
            cust_fil = flag.rm or "disabled__"
            cust_fil += str().join(
                f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
            )
        else:
            cust_fil = str_esc(flag.f)
        anilist = flag.da
        cust_v = flag.v
        force_name = flag.n
        if flag.s and not flag.s.isdigit():
            return await event.reply("`Value for '-s' arg has to be digit.`")
    try:
        if event.is_reply:
            rep_event = await event.get_reply_message()
            if rep_event.file:
                return await event.reply("**Error:** `Use /add for files instead.`")
            if args:
                if not args.isdigit():
                    return await event.reply(
                        f"**Yeah No.**\n`Error: expected a number but received '{args}'.`"
                    )
                if flag.b and not flag.y:
                    await event.reply(
                        "Warning: '-b' flag ignored!\nAdd -y to bypass this warning."
                    )
                if flag.s and not flag.y:
                    await event.reply(
                        "Warning: '-s' flag ignored!\nAdd -y to bypass this warning."
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
                        file = await get_torrent(uri)
                        if file.error:
                            await event2.reply(file.error, quote=True)
                            await asyncio.sleep(10)
                            continue
                        if (flag.b and flag.y) and file.count > 1:
                            file.name = flag.d or file.name
                            mode = "Batch."
                            force_name = None
                        elif (flag.s and flag.y) and file.count > 1:
                            if (ind := int(flag.s)) > (file.count - 1):
                                await event2.reply(
                                    f"'-s': `{flag.s} is more than last file_id :- {file.count - 1}\n"
                                    f"Total files in folder :- {file.count}`"
                                )
                                await asyncio.sleep(5)
                                continue
                            if not is_video_file(file.file_list[ind]):
                                await event2.reply("'-s': " + no_fl_spt_msg)
                                await asyncio.sleep(5)
                                continue
                            mode = f"Select. {flag.s}"
                            file.name = flag.d or (file.file_list[ind].split("/"))[-1]
                        if file.count > 1:
                            await event2.reply(no_bt_spt_msg, quote=True)
                            await asyncio.sleep(3)
                            continue
                        if not is_video_file(file.name):
                            await event2.reply(no_fl_spt_msg, quote=True)
                            await asyncio.sleep(5)
                            continue
                        already_in_queue = False
                        for item in queue.values():
                            if file.name in item:
                                await event2.reply(
                                    "**THIS LINK HAS ALREADY BEEN ADDED TO QUEUE**",
                                    quote=True,
                                )
                                await asyncio.sleep(5)
                                already_in_queue = True
                                break
                        if already_in_queue:
                            continue
                        if file.count > 1 and (flag.b and flag.y):
                            result = await batch_preview(
                                event2,
                                file,
                                chat_id,
                                event2.id,
                                cust_v or get_v(),
                                cust_fil or get_f(),
                                user=user_id,
                                select_all=flag.y,
                            )
                            if not result:
                                await event2.reply(
                                    "'-b': `Not added to queue due to unknown error!`"
                                )
                                await asyncio.sleep(5)
                                continue
                        if not bot_is_paused():
                            pause(status=dl_pause)

                        queue.update(
                            {
                                (chat_id, event2.id): [
                                    file.name,
                                    (user_id, event2),
                                    (
                                        cust_v or get_v(),
                                        cust_fil or get_f(),
                                        ("qbit", mode),
                                        force_name,
                                        (anilist, uri),
                                    ),
                                ]
                            }
                        )
                        await save2db()

                        msg = await event2.reply(
                            f"**Link added to queue ⏰, POS:** `{len(queue)-1}`\n`Please Wait , Encode will start soon`",
                            quote=True,
                        )
                        await asyncio.sleep(5)
                    if len(queue) > 1:
                        asyncio.create_task(listqueue(msg, None, event.client, False))
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
        file = await get_torrent(uri)
        if file.error:
            return await event.reply(f"`{file.error}`")
        if flag and flag.b and file.count > 1:
            file.name = flag.d or file.name
            mode = "Batch."
            force_name = None
        elif flag and flag.s and file.count > 1:
            if (ind := int(flag.s)) > (file.count - 1):
                return await event.reply(
                    f"'-s': `{flag.s} is more than last file_id :- {file.count - 1}\n"
                    f"Total files in folder :- {file.count}`"
                )
            if not is_video_file(file.file_list[ind]):
                return await event.reply("'-s': " + no_fl_spt_msg)
            mode = f"Select. {flag.s}"
            file.name = flag.d or (file.file_list[ind].split("/"))[-1]
        elif file.count > 1:
            return await event.reply(no_bt_spt_msg)
        elif not is_video_file(file.name):
            return await event.reply(no_fl_spt_msg)
        for item in queue.values():
            if file.name in item:
                return await event.reply(
                    "**THIS TORRENT HAS ALREADY BEEN ADDED TO QUEUE**"
                )
        if file.count > 1 and (flag and flag.b):
            result = await batch_preview(
                event,
                file,
                chat_id,
                event.id,
                cust_v or get_v(),
                cust_fil or get_f(),
                user=user_id,
                select_all=flag.y,
            )
            if not result:
                return await or_event.delete()
        async with queue_lock:
            queue.update(
                {
                    (chat_id, event.id): [
                        file.name,
                        (user_id, None),
                        (
                            cust_v or get_v(),
                            cust_fil or get_f(),
                            ("qbit", mode),
                            force_name,
                            (anilist, uri),
                        ),
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
    except Exception as e:
        await logger(Exception)
        await rm_pause(dl_pause)
        return await event.reply(f"An error Occurred.\n - {e}")


async def enselect(event, args, client):
    """
    Select files in batch to encode or skip;
    flags:
        --all "enable" or "disable"
            select or deselect all files in a batch respectively.
        -e with a list of file_ids to encode
        -d with a list of file_ids to skip
    file_ids:- numbers next to the files in batch preview
    list:- numbers separated by spaces (must be in quotes)
    *Requires a batch preview to be active.
    */batch
    """
    user = event.sender_id
    if not (user_is_owner(user) or user == get_previewer()):
        return await try_delete(event)
    preview_list = get_preview(list=True)
    preview_queue = get_preview()
    if not preview_list:
        return await event.reply("`Nothing to Select.`")
    try:
        flag, args = get_args("-e", "-d", "--all", to_parse=args, get_unknown=True)
        if not (flag.d or flag.e or flag.all):
            return await event.reply(f"`{enselect.__doc__}`")
        err = str()
        msg = str()
        sall = None
        if flag.all:
            if flag.all.casefold() == "disable":
                msg = "`Unselected all files.`"
                sall = 0
            elif flag.all.casefold() == "enable":
                msg = "`Selected all files`"
                sall = 1
            else:
                return await event.reply(f"`Invalid argument '{flag.all}' for --all.`")
            for i in list(preview_queue.keys()):
                v = preview_queue.get(i)
                if v != 3:
                    preview_queue.update({i: sall})
            reply = await event.reply(msg)
            await asyncio.sleep(10)
            await reply.delete()
            return await try_delete(event)
        if flag.e:
            if valid_range(flag.e):
                _start, _end = map(int, flag.e.split("-"))
                enable_list = [str(x) for x in range(_start, (_end + 1))]
            else:
                enable_list = flag.e.split()
            msg += "**Will Encode:**\n"
            for i in enable_list:
                i = int(i) if i.isdigit() else i
                v = preview_queue.get(i, False)
                if v is False:
                    err += f"'{i}' - doesn't exist/not a valid index number.\n\n"
                elif v == 3:
                    err += (
                        f"{i} - `{preview_list[i].split('/')[-1]}` is not a video.\n"
                        "   State cannot be changed for non videos.\n\n"
                    )
                else:
                    preview_queue.update({i: 1})
                    msg += f"{i} - `{preview_list[i].split('/')[-1]}`\n    **Changed from:** '{sdict.get(v)}'"
                    msg += "\n\n"
            msg += "\n"
        if flag.d:
            if valid_range(flag.d):
                _start, _end = map(int, flag.d.split("-"))
                disable_list = [str(x) for x in range(_start, (_end + 1))]
            else:
                disable_list = flag.d.split()
            msg += "**Will Skip:-**\n"
            for i in disable_list:
                i = int(i) if i.isdigit() else i
                v = preview_queue.get(i, False)
                if v is False:
                    err += f"'{i}' - doesn't exist/not a valid index number.\n\n"
                elif v == 3:
                    err += (
                        f"{i} - `{preview_list[i].split('/')[-1]}` is not a video.\n"
                        "   State cannot be changed for non videos.\n\n"
                    )
                else:
                    preview_queue.update({i: 0})
                    msg += f"{i} - `{preview_list[i].split('/')[-1]}`\n    **Changed from:** '{sdict.get(v)}'"
                    msg += "\n\n"
        if err:
            msg += "\n**Errors:**\n"
            msg += err

        replies = []
        for msg_ in await split_text(msg):
            reply = await event.reply(msg)
            replies.append(reply)
        await asyncio.sleep(10)
        for reply in replies:
            await try_delete(reply)
        await try_delete(event)
    except Exception:
        await logger(Exception)


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
        anilist = True
        cust_fil = cust_v = str()
        force_name = None
        uri = None
        if args:
            if not flag:
                flag, args = get_args(
                    ["-da", "store_false"],
                    "-f",
                    "-rm",
                    "-n",
                    "-tc",
                    "-tf",
                    "-v",
                    to_parse=args,
                    get_unknown=True,
                )
            if flag.rm or flag.tc or flag.tf:
                cust_fil = flag.rm or "disabled__"
                cust_fil += str().join(
                    f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
                )
            else:
                cust_fil = str_esc(flag.f)
            anilist = flag.da
            cust_v = flag.v
            force_name = flag.n
        queue.update(
            {
                (chat_id, message.id): [
                    name,
                    (sender_id, message),
                    (
                        cust_v or get_v(),
                        cust_fil or get_f(),
                        ("tg", "None"),
                        force_name,
                        (anilist, uri),
                    ),
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
        media = await message._client.get_messages(message.chat.id, message.id + 1)
        if media.empty or not (media.document or media.video):
            return
        await asyncio.sleep(3)
        asyncio.create_task(pencode(media, args, sender_id, flag))
        return


async def addqueue(event, args, client):
    """
    Add replied video to queue with args
    Accepts the same argument as /l
    can also be used to reuse a leech command
        if user is OWNER
    """
    user_id = event.sender_id
    if not user_is_allowed(user_id):
        return
    if not event.is_reply:
        return event.reply("Command needs to be a replied message.")
    try:
        event_2 = await event.get_reply_message()
        if event_2.file:
            media = await client.get_messages(event.chat_id, event_2.id)
            if media.empty:
                return await event.reply("Try again!")
            await pencode(media, args, user_id)
            return
        if not user_is_owner(user_id):
            return
        command, args = (
            event_2.text.split(maxsplit=1)
            if (event_2.text and len(event_2.text.split()) > 1)
            else (event_2.text, None)
        )
        if not (command and check_cmds(command, "/l", "/ql", "/qbleech", "/leech")):
            return await event.reply(addqueue.__doc__)
        if check_cmds(command, "/l", "/leech"):
            asyncio.create_task(enleech(event_2, args, client, True))
        elif check_cmds(command, "/ql", "/qbleech"):
            asyncio.create_task(enleech2(event_2, args, client, True))
    except Exception:
        await logger(Exception)
    finally:
        await try_delete(event)


async def clearqueue(event, args, client):
    """
    Clears an item or all items from queue
    Now requires an argument to prevent accidents.
        - pass a number or a range of numbers representing a queue item or queue items to remove __(check with queue)__
        - pass 'all' (not case sensitive) remove all 'pending' queue items
            if bot is paused, removes all queue items.
    """
    user = event.sender_id
    if not user_is_allowed(user):
        return await try_delete(event)

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
        await clean_batch(i)
        async with queue_lock:
            queue.pop(list(queue.keys())[i])
        await event.reply(f"`{q_values[0]}` has been removed from queue")
        await save2db()
        return await save2db("batches")
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
            await clean_batch(key=key)
        if not reply:
            return await event.reply("`Nothing was cleared.`")
        msg = await event.reply(btch_clr_msg + reply)
    elif args.casefold() == "all":
        reply = str()
        s = 0 if get_pause_status() == 0 else 1
        for key, i in zip(list(queue.keys())[s:], itertools.count(start=1)):
            adder = (queue.get(key)[1])[0]
            if not user_is_owner(user) and user != adder:
                continue
            reply += "{0}. `{1}`\n".format(i, queue.get(key)[0])
            async with queue_lock:
                queue.pop(key)
            await clean_batch(key=key)
        if not reply:
            return await event.reply("`Nothing was cleared.`")
        msg = await event.reply(btch_clr_msg + reply)
    elif not args.isdigit():
        return await event.reply(
            "`Pass a number/range/all for an item/items on queue to be removed.`"
        )

    await save2db()
    await save2db("batches")
    await asyncio.sleep(7)
    await try_delete(event)
    await msg.delete()
    return


async def edit_batch(event, args, client):
    """
    Command for viewing queued batches;
    args:
        None - view number of queued batches
        queue number (id) of the batch :- check with /queue
            - enables live preview for the batch.
    """
    user = event.sender_id
    if not user_is_allowed(user):
        return await try_delete(event)
    batch_queue = get_bqueue()
    queue = get_queue()
    try:
        if not batch_queue:
            return await event.reply("`There are no queued batches.`")
        if not args:
            return await event.reply(
                f"There are `{len(batch_queue)}` queued batches."
                "\nTo view, pass the queue number of the batch on the original queue."
            )
        if not (args.isdigit() and int(args) <= (len(queue) - 1)):
            return await event.reply(f"`{edit_batch.__doc__}`")
        args = int(args)
        key = list(queue.keys())[args]
        name, s_msg, vfm = queue.get(key)
        if not (user_is_owner(user) or user == s_msg[0]):
            return await event.reply("`This batch wasn't added to queue by you.`")
        v, f, m, n, au = vfm
        if not (value := batch_queue.get(key)):
            return await event.reply(f"'{args}' - not a batch queue item")
        result = await batch_preview(event, value[0], key[0], key[1], v, f, reuse=True)
        if result:
            return await event.reply(f"Edited batch:- `{name}` successfully!")
        else:
            return await try_delete(event)
    except Exception:
        await logger(Exception)


async def edit_queue(event, args, client):
    """
    Edit configuration of items already in queue:
    arguments:
        -f <filter> (*raw filter) [low priority]
            to disable filter pass *'None'
        -a enable anilist (Higher priority)
        -d "new file name for item in queue"
        -da disable anilist (Lower priority)
        -n outputfile.mkv to force an output filename
        -q <int> (id of queue item to edit)
            can be checked with /queue command
            can also be passed without flags
        -rm <filter> (what_to_remove)
        -tc <filter> (tag_caption_as)
        -tf <filter> (tag_file_as)
        -u (for debugging) change uri
        -v <version> (tag file with version)
            to disable versioning pass 'None'

    *raw filter format:-
    what_to_remove\\ntag_file_as\\ntag_caption_as

    *passing 'off' and 'disable' also serve as a method to disable
    """
    user = event.sender_id
    if not user_is_allowed(user):
        return
    queue = get_queue()
    if not queue:
        return await event.reply("`No items on queue.`")
    try:
        cust_fil = cust_v = str()
        flag, args = get_args(
            ["-a", "store_true"],
            "-d",
            ["-da", "store_true"],
            ["-e", "store_true"],
            "-f",
            "-n",
            "-q",
            "-rm",
            "-tc",
            "-tf",
            "-u",
            "-v",
            to_parse=args,
            get_unknown=True,
        )
        args = flag.q or args
        if not args.isdigit():
            return await event.reply(
                "Queue id must be a digit\n\n" f"**HELP:**\n`{edit_queue.__doc__}`"
            )
        args = int(args)
        if args > (len(queue) - 1):
            return await event.reply("`Kindly pass a valid queue number.`")

        if flag.rm or flag.tc or flag.tf:
            cust_fil = flag.rm or "disabled__"
            cust_fil += str().join(
                f"\n{x}" if x else "\nauto" for x in [flag.tf, flag.tc]
            )
        else:
            cust_fil = str_esc(flag.f)
        cust_v = flag.v
        file_name, s_msg, v_f_m = list(queue.values())[args]
        if not (user_is_owner(user) or user == s_msg[0]):
            return await event.reply("`This item wasn't added to queue by you.`")
        key = list(queue.keys())[args]
        v, f, m, n, au = v_f_m
        anilist, uri = au
        anilist = (flag.a or flag.da) or anilist
        if flag.f and flag.f.casefold() in ("none", "disable", "off"):
            cust_fil = f = None
        if flag.v and flag.v.casefold() in ("none", "disable", "off"):
            cust_v = v = None
        uri = flag.u or uri
        queue.update(
            {
                key: [
                    flag.d or file_name,
                    s_msg,
                    (cust_v or v, cust_fil or f, m, flag.n or n, (anilist, uri)),
                ]
            }
        )
        await save2db()
        await save2db("batches")
        await event.reply("`Edited queued item successfully.`")
    except Exception as e:
        await event.reply(f"An error occurred\n  - {str(e)}")
        await logger(Exception)
