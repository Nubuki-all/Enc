import asyncio
from functools import partial

import pyrogram

from bot import *
from bot.config import _bot, conf
from bot.fun.emojis import enmoji, enmoji2
from bot.fun.quips import enquip3
from bot.fun.quotes import enquotes
from bot.others.exceptions import ArgumentParserError

from .bot_utils import get_pause_status, gfn, is_url, sync_to_async
from .log_utils import log, logger
from .os_utils import s_remove


def user_is_allowed(user: str | int):
    user = str(user)
    return user in conf.OWNER or user in _bot.temp_users


def user_is_owner(user: str | int):
    user = str(user)
    return user in conf.OWNER


def user_is_dev(user):
    user = int(user)
    return user == conf.DEV


def pm_is_allowed(in_group=False, in_pm=False):
    if in_pm:
        return not conf.NO_TEMP_PM
    if in_group:
        return _bot.temp_only_in_group


def temp_is_allowed(user: str | int):
    user = str(user)
    return user in _bot.temp_users


def turn(turn_id: str = None):
    if turn_id:
        return turn_id in _bot.r_queue
    return _bot.r_queue


async def wait_for_turn(turn_id: str, msg):
    cancel_button = InlineKeyboardButton(
        text=f"Cancel", callback_data=f"cancel_turn {turn_id}"
    )
    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    await msg.edit_reply_markup(reply_markup=reply_markup)
    while turn(turn_id):
        await asyncio.sleep(5)
        if _bot.r_queue[0] == turn_id:
            await msg.delete()
            return 1


def waiting_for_turn():
    return turn() and len(turn()) > 1


async def clean_old_message(e, pyro=False):
    await e.answer("⛔ Old button.  Removing…")
    await asyncio.sleep(5)
    await e.delete() if not pyro else await e.message.delete()
    return


async def try_delete(msg):
    try:
        await msg.delete()
    except errors.rpcerrorlist.MessageDeleteForbiddenError:
        await msg.reply(f"`{enquip3()}`")
    except pyro_errors.exceptions.forbidden_403.MessageDeleteForbidden:
        await msg.reply(f"`{enquip3()}`", quote=True)
    except Exception:
        await logger(Exception)


async def get_cached(dl: str, sender, user: int, e, op):
    try:
        dl_check = Path(dl)
        dl_check2 = Path(dl + ".temp")
        if dl_check.is_file():
            await e.edit("`Using cached download…`")
            if op:
                await op.edit("`Using cached download…`")
            await asyncio.sleep(3)
        if dl_check2.is_file():
            prog_msg = f"{enmoji()} Waiting for download to complete"
            false_prog = "..."
            while dl_check2.is_file():
                try:
                    false_prog = "..." if len(false_prog) > 20 else false_prog
                    await e.edit("`" + prog_msg + false_prog + "`")
                    if op:
                        await asyncio.sleep(3)
                        await op.edit(
                            f"{enmoji()} `Waiting for` [{sender.first_name}'s](tg://user?id={user}) `download to complete{false_prog}`"
                        )
                    false_prog += "."
                    await asyncio.sleep(15)
                except errors.rpcerrorlist.MessageNotModifiedError:
                    await asyncio.sleep(15)
                    continue
                except errors.FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    continue
        # CACHE_QUEUE.clear()
        _bot.cached = False
        if not dl_check.is_file():
            raise Exception("Getting cached file failed\nfile might have been deleted.")
        return True
    except Exception:
        await logger(Exception)
        await e.edit("`Using cached download failed\nRe-downloading…`")
        if op:
            await op.edit("`Using cached download failed\nRe-downloading…`")
        # CACHE_QUEUE.clear()
        _bot.cached = False
        return False


def valid_range(args: str):
    if isinstance(args, str):
        return (
            len(args.split("-")) == 2
            and (args.split("-")[0].strip()).isdigit()
            and (args.split("-")[1].strip()).isdigit()
            and args.split("-")[0].strip() != args.split("-")[1].strip()
        )


async def enpause(message):
    pause_msg = (
        " `Bot has been paused to continue, unpause bot using the /pause command`"
    )
    while _bot.paused:
        if get_pause_status() == "rss":
            if len(_bot.paused) == 1:
                break
        try:
            await message.edit(enmoji() + pause_msg)
            await asyncio.sleep(10)
        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except pyro_errors.BadRequest:
            await asyncio.sleep(10)
            continue
        except Exception:
            await logger(Exception)


def get_expanded_chats(chats):
    expanded_chat = []
    for chat in chats:
        (
            expanded_chat.append(str(chat))
            if chat
            else expanded_chat.extend(conf.RSS_CHAT.split())
        )
    return expanded_chat


async def send_rss(msg: str, chat_ids: list = None):
    try:
        chats = (
            [chat_ids] if not isinstance(chat_ids, list) else chat_ids
        )  # backward compatibility
        for chat in get_expanded_chats(chats):
            top_chat = chat.split(":")
            chat, top_id = (
                map(int, top_chat) if len(top_chat) > 1 else (int(top_chat[0]), None)
            )
            event = await avoid_flood(tele.send_message, chat, msg, reply_to=top_id)
        return event
    except Exception:
        await logger(Exception)


async def avoid_flood(func, *args, **kwargs):
    try:
        pfunc = partial(func, *args, **kwargs)
        return await pfunc()
    except errors.FloodWaitError as e:
        log(
            e=f"Sleeping for {e.seconds}s due to floodwait!"
            "\n"
            f"Caused by: {gfn(avoid_flood)}"
        )
        await asyncio.sleep(e.seconds)
        return await avoid_flood(func, *args, **kwargs)
    except pyro_errors.FloodWait as e:
        log(
            e=f"Sleeping for {e.value}s due to floodwait!"
            "\n"
            f"Caused by: {gfn(avoid_flood)}"
        )
        await asyncio.sleep(e.value)
        return await avoid_flood(func, *args, **kwargs)


async def edit_message(message, text: str):
    """
    A function to edit message with a loop in the event of a FloodWait
    """
    try:
        edited = await message.edit(text)
    except pyro_errors.FloodWait as e:
        log(
            e=f"Sleeping for {e.value}s due to floodwait!"
            "\n"
            f"Caused by: {gfn(edit_message)}"
        )
        await asyncio.sleep(e.value)
        return await edit_message(message, text)
    except errors.FloodWaitError as e:
        log(
            e=f"Sleeping for {e.seconds}s due to floodwait!"
            "\n"
            f"Caused by: {gfn(edit_message)}"
        )
        await asyncio.sleep(e.seconds)
        return await edit_message(message, text)
    except Exception:
        await logger(Exception)

    return edited


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def line_split(line):
    return [t.strip("\"'") for t in re.findall(r'[^\s"]+|"[^"]*"', line)]


def get_args(*args, to_parse: str, get_unknown=False):
    parser = ThrowingArgumentParser(
        description="parse command flags", exit_on_error=False, add_help=False
    )
    for arg in args:
        if isinstance(arg, list):
            parser.add_argument(arg[0], action=arg[1], required=False)
        else:
            parser.add_argument(arg, type=str, required=False)
    flag, unknowns = parser.parse_known_args(line_split(to_parse))
    if get_unknown:
        unknown = " ".join(map(str, unknowns))
        return flag, unknown
    return flag


async def reply_message(message, text, quote=True):
    """A function to reply messages with a loop in the event of FloodWait"""
    if isinstance(message, pyrogram.types.Message):
        try:
            replied = await message.reply(text, quote=quote)
        except pyro_errors.FloodWait as e:
            log(
                e=f"Sleeping for {e.value}s due to floodwait!"
                "\n"
                f"Caused by: {gfn(reply_message)}"
            )
            await asyncio.sleep(e.value)
            return await reply_message(message, text, quote)

    else:
        try:
            replied = (
                await message.reply(text) if quote else await message.respond(text)
            )
        except errors.FloodWaitError as e:
            log(
                e=f"Sleeping for {e.seconds}s due to floodwait!"
                "\n"
                f"Caused by: {gfn(reply_message)}"
            )
            await asyncio.sleep(e.seconds)
            return await reply_message(message, text, quote)

    return replied


async def bc_msg(text, except_user=None, mlist=[]):
    """Broadcast a message to every registered user in bot and optionally return a list of the messages"""
    for u in conf.OWNER.split():
        if except_user == (u := int(u)):
            continue
        try:
            e = await pyro.send_message(u, text)
            mlist.append(e)
        except Exception:
            log(Exception)

    for u in _bot.temp_users:
        if except_user == (u := int(u)):
            continue
        try:
            e = await pyro.send_message(u, text)
            mlist.append(e)
        except Exception:
            pass
            # log(Exception)
    if conf.LOG_CHANNEL:
        try:
            e = await pyro.send_message(
                conf.LOG_CHANNEL,
                text,
            )
            mlist.append(e)
        except Exception:
            log(Exception)
    return mlist


async def report_encode_status(
    process,
    _id,
    stderr,
    msg,
    user,
    file=None,
    _is="Encoding",
    msg_2_delete=None,
    log_msg=None,
    pyro_msg=False,
    stdout=None,
    exe_prefix="ffmpeg",
):
    _dir, file = os.path.split(file)
    if msg_2_delete:
        await msg_2_delete.delete()
    cancelled = None
    log_id = None
    reportee = None
    if log_msg:
        log_id = f"{log_msg.chat_id}:{log_msg.id}"
    if process.returncode != 0:
        reply = f"{_is} "
        if file:
            reply += f"of `{file}` "
        if _bot.e_cancel.get(_id) or (log_id and _bot.e_cancel.get(log_id)):
            cancelled = True
            reply += f"was cancelled. ❌"
            who_cancel = _bot.e_cancel.get(_id)
            who_cancel = _bot.e_cancel.get(log_id) if not who_cancel else who_cancel
            if who_cancel != user:
                canceller = await pyro.get_users(who_cancel)
                if not pyro_msg:
                    reply += (
                        f" by [{canceller.first_name}.](tg://user?id={canceller.id})"
                    )
                else:
                    reply += f"by {canceller.mention()}."
        else:
            reply += f"Failed. {enmoji2()}\nLogs available below."
            if _bot.report_failed_enc and user:
                reportee = int(conf.OWNER.split()[0])
                chat = msg.chat_id if not pyro_msg else msg.chat.id
                if reportee == int(chat):
                    reportee = None

        reply += "!"
        if reportee:
            report = await tele.send_message(reportee, reply)
        if not pyro_msg:
            await msg.edit(reply, buttons=None)
        else:
            await msg.edit(reply)
        await asyncio.sleep(3)

        if log_msg:
            await log_msg.edit(reply, buttons=None)
        er = stderr.decode()
        if stdout and (out := stdout.decode()):
            er += "\n" + out
        error = None
        msg_2_delete = msg_2_delete or msg
        if len(er) > 4095 and not cancelled:
            out_file = f"{exe_prefix}_error.txt"
            with open(out_file, "w") as file:
                file.write(er)
            error = await msg_2_delete.reply(
                file=out_file,
                force_document=True,
            )
            s_remove(out_file)
        elif not cancelled and er:
            error = await msg.reply(f"`{er}`")
        elif not cancelled:
            error = await msg.reply("`Couldn't get ffmpeg error\ncheck logs.`")
            log(er)
        if error and log_msg:
            await log_msg.reply(error)
        if error and reportee:
            await report.reply(error)
    else:
        reply = f"**{_is}** "
        if file:
            reply += f"**of** `{file}`"
        reply += " **was successful!.**"
        await msg.edit(reply)
        await asyncio.sleep(3)
        await log_msg.edit(reply, buttons=None) if log_msg else None
    await asyncio.sleep(5)


async def report_failed_download(download, msg, file, user=None):
    pyro_msg = True if isinstance(msg, pyrogram.types.Message) else False
    reply = f"Download of `{file}` "
    if download.is_cancelled:
        reply += "was cancelled."
        if download.canceller and (
            not user or (user and download.canceller.id != user)
        ):
            reply += " by "
            if not pyro_msg:
                reply += f"[{download.canceller.first_name}](tg://user?id={user})"
            else:
                reply += download.canceller.mention()
    else:
        reply += f"failed.\n- `{download.download_error}`"
    reply += "!"
    if not download.is_cancelled and user and _bot.report_failed_dl:
        reportee = int(conf.OWNER.split()[0])
        chat = msg.chat_id if not pyro_msg else msg.chat.id
        if not reportee == int(chat):
            await tele.send_message(reportee, reply)
    return await msg.edit(reply)


async def msg_sleep_delete(message, text, edit=False, time=10, del_rep=False):
    """Reply a message, sleeps for specified time then deletes message"""
    msg = (
        await reply_message(message, text)
        if not edit
        else await edit_message(message, text)
    )
    await asyncio.sleep(time)
    if del_rep:
        await try_delete(message)
    return await msg.delete()


async def get_message_from_link(link, pyrogram=True):
    if not is_url(link):
        return None
    try:
        chat_id = link.split("/")[-2]
        chat_id = int("-100" + str(chat_id)) if chat_id.isdigit() else chat_id
        msg_id = int(link.split("/")[-1])
        if pyrogram:
            message = await pyro.get_messages(chat_id, msg_id)
        else:
            message = await tele.get_messages(chat_id, ids=msg_id)
    except Exception:
        message = None
    return message


async def enquoter(msg, rply):
    try:
        quotes = await sync_to_async(enquotes)
        await rply.edit(f"**{msg}**\n\n~while you wait~\n\n{quotes}")
        await asyncio.sleep(1.5)
    except Exception:
        await logger(Exception)


async def event_handler(
    event,
    function,
    client=None,
    require_args=False,
    disable_help=False,
    split_args=" ",
    default_args: str = False,
    use_default_args=False,
):
    args = (
        event.text.split(split_args, maxsplit=1)[1].strip()
        if len(event.text.split()) > 1
        else None
    )
    args = default_args if use_default_args and default_args is not False else args
    help_tuple = ("--help", "-h")
    if (
        (require_args and not args)
        or (args and args.casefold() in help_tuple)
        or (require_args and not (default_args or default_args is False))
        or (default_args in help_tuple)
    ):
        if disable_help:
            return
        return await reply_message(event, f"`{function.__doc__}`")
    await function(event, args, client)
