from .funcn import *
from telethon import events
from telethon.tl.custom import Button
from telethon.tl.types import InlineKeyboardButton, InlineKeyboardMarkup

status_lock = asyncio.Lock()

STATUS_START = 0
PAGES = 1
PAGE_NO = 1
STATUS_LIMIT = 10

async def queue_status(event):
    try:
        async with status_lock:
            if QUEUE_STATUS:
                for q_id in QUEUE_STATUS:
                    _chat_id, _msg_id = q_id.split()
                    if event.chat_id == int(_chat_id):
                        msg = await app.get_messages(int(_chat_id), int(_msg_id))
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                        QUEUE_STATUS.remove(q_id)
                return QUEUE_STATUS.append(str(event.chat_id) + " " + str(event.id))
            else:
                QUEUE_STATUS.append(str(event.chat_id) + " " + str(event.id))
    except Exception:
        er = traceback.format_exc()
        LOGS.info(er)
        await channel_log(er)

async def get_queue():
    msg = ""
    button = None
    try:
        i = len(QUEUE)
        globals()['PAGES'] = (i + STATUS_LIMIT - 1) // STATUS_LIMIT
        if PAGE_NO > PAGES and PAGES != 0:
            globals()['STATUS_START'] = STATUS_LIMIT * (PAGES - 1)
            globals()['PAGE_NO'] = PAGES
        for file in list(QUEUE.values())[STATUS_START:STATUS_LIMIT+STATUS_START]:
            file_name, _id = file
            file_id = list(QUEUE.keys())[list(QUEUE.values()).index(file)]
            if str(_id).startswith("-100"):
                msg = await app.get_messages(_id, int(file_id))
                user = msg.from_user
                if user is None:
                    if UNLOCK_UNSTABLE:
                        user = await app.get_users(777000)
                    else:
                        user = await app.get_users(OWNER.split()[0])
            else:
                user = await app.get_users(_id)
            msg += f"{i}. `{file_name}`\n**Added by:** [{user.first_name}](tg://user?id={_id})\n"

        if msg:
            msg += f"\n**{enmoji()} Tip: To remove an item from queue use** /clear <queue number>"
        else:
            msg = "**Nothing Here** 🐱"
        if i > STATUS_LIMIT:
            msg += f"**Page:** {PAGE_NO}/{PAGES} | **Pending Tasks:** {i}\n"
            # Define the buttons
            #btn_prev = InlineKeyboardButton("<<", callback_data="status prev")
            #btn_next = InlineKeyboardButton(">>", callback_data="status next")
            #btn_refresh = InlineKeyboardButton("♻️", callback_data="status ref")
            # Define the button layout
            #button_layout = [
            #    [btn_prev, btn_next],
            #    [btn_refresh]
            ]
            # Create the InlineKeyboardMarkup
            #button = InlineKeyboardMarkup(button_layout)
            btn_prev = Button.inline("<<", data="status prev")
            btn_next = Button.inline(">>", data="status next")
            btn_refresh = Button.inline("♻️", data="status")
            # Define the button layout
            button = [([btn_prev, btn_next]), [btn_refresh],]
        else:
            msg += f"**Pending Tasks:** {i}\n"

    except Exception:
        er = traceback.format_exc()
        LOGS.info(er)
        await channel_log(er)
        msg = "__An error occurred.__"
    return msg, button 


async def turn_page(event):
    data = event.data.decode()
    global STATUS_START, PAGE_NO
    async with status_lock:
        if data[1] == "status next":
            if PAGE_NO == PAGES:
                STATUS_START = 0
                PAGE_NO = 1
            else:
                STATUS_START += STATUS_LIMIT
                PAGE_NO += 1
        elif data[1] == "status prev":
            if PAGE_NO == 1:
                STATUS_START = STATUS_LIMIT * (PAGES - 1)
                PAGE_NO = PAGES
            else:
                STATUS_START -= STATUS_LIMIT
                PAGE_NO -= 1


pattern = re.compile(r"^status")
@events.register(events.CallbackQuery(pattern=pattern))
async def callback_query_handler(event):
    async def _(e):
        await turn_page(e)