from telethon import events

from bot import Button, conf, itertools, pyro, queue_lock, re, tele
from bot.config import _bot

from .log_utils import logger

STATUS_START = 1
PAGES = 1
PAGE_NO = 1
STATUS_LIMIT = 10


async def q_dup_check(event):
    try:
        if _bot.queue_status:
            check = True
            for q_id in _bot.queue_status:
                _q_id = str(event.chat_id) + " " + str(event.id)
                if q_id == _q_id:
                    check = False
        else:
            check = True
    except Exception:
        check = True
        await logger(Exception)
    return check


async def queue_status(event):
    try:
        if _bot.queue_status:
            for q_id in _bot.queue_status:
                _chat_id, _msg_id = q_id.split()
                if event.chat_id == int(_chat_id):
                    msg = await pyro.get_messages(int(_chat_id), int(_msg_id))
                    try:
                        await msg.delete()
                    except Exception:
                        pass
                    _bot.queue_status.remove(q_id)
            return _bot.queue_status.append(str(event.chat_id) + " " + str(event.id))
        else:
            _bot.queue_status.append(str(event.chat_id) + " " + str(event.id))
    except Exception:
        await logger(Exception)


async def get_queue_msg():
    msg = str()
    button = None
    cmd_s = conf.CMD_SUFFIX.strip()
    try:
        i = len(_bot.queue)
        globals()["PAGES"] = (i + STATUS_LIMIT - 2) // STATUS_LIMIT
        if PAGE_NO > PAGES and PAGES != 0:
            globals()["STATUS_START"] = (STATUS_LIMIT * PAGES) - 9
            globals()["PAGE_NO"] = PAGES

        for file, _no in zip(
            list(_bot.queue.values())[STATUS_START : STATUS_LIMIT + STATUS_START],
            itertools.count(STATUS_START),
        ):
            file_name, u_msg, ver_fil = file
            chat_id, msg_id = list(_bot.queue.keys())[
                list(_bot.queue.values()).index(file)
            ]
            user_id, message = u_msg
            user_id = (
                777000 if not user_id or str(user_id).startswith("-100") else user_id
            )
            user = await pyro.get_users(user_id)
            ver, fil, mode, rname, ani_uri = ver_fil

            if fil and len(fil.split("\n")) > 2:
                rm, ftag, ctag = fil.split("\n", maxsplit=2)
                fil = f"[-rm: `{rm}`, -tf: `{ftag}`, -tc: `{ctag}`]"

            batch = "  ├**Batch:** Yes\n" if mode[1].lower() == "batch." else ""
            force_rnm = f"  ├**Force rename to:** `{rname}`\n" if rname else ""
            anilist = "  ├**Anilist:** Off\n" if not ani_uri[0] else ""

            msg += (
                f"{_no}. `{file_name}`\n  ├**Filter:** {fil}\n  ├**Release version:** {ver}\n"
                f"{batch}{force_rnm}{anilist}"
                f"  └**Added by:** [{user.first_name}](tg://user?id={user_id})\n\n"
            )

        if not msg:
            return None, None
        if (i - 1) > STATUS_LIMIT:
            # Create the Inline button
            btn_prev = Button.inline("<<", data="status prev")
            btn_info = Button.inline(f"{PAGE_NO}/{PAGES} ({i - 1})", data="status 🙆")
            btn_next = Button.inline(">>", data="status next")
            # Define the button layout
            button = [[btn_prev, btn_info, btn_next]]
        else:
            msg += f"**Pending Tasks:** {i - 1}\n"
        msg += f"\n**📌 Tip: To remove an item from queue use** /clear{cmd_s} <queue number>"

    except Exception:
        await logger(Exception)
        msg = "__An error occurred.__"
    return msg, button


async def turn_page(event):
    try:
        data = event.pattern_match.group(1).decode().strip()
        global STATUS_START, PAGE_NO, PAGES
        async with queue_lock:
            if data == "next":
                if PAGE_NO == PAGES:
                    STATUS_START = 1
                    PAGE_NO = 1
                else:
                    STATUS_START += STATUS_LIMIT
                    PAGE_NO += 1
            elif data == "prev":
                if PAGE_NO == 1:
                    STATUS_START = (STATUS_LIMIT * (PAGES - 1)) + 1
                    PAGE_NO = PAGES
                else:
                    STATUS_START -= STATUS_LIMIT
                    PAGE_NO -= 1

        await event.answer(f"{data}…")

    except Exception:
        await logger(Exception)


tele.add_event_handler(
    turn_page, events.callbackquery.CallbackQuery(data=re.compile(b"status(.*)"))
)
