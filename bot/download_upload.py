import uuid

from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from .funcn import *


class uploader:
    def __init__(self, bot, app, sender=123456):
        self.bot = bot
        self.app = app
        self.sender = int(sender)
        self.callback_data = "cancel_upload" + str(uuid.uuid4())
        self.is_cancelled = False
        self.canceller = None
        self.handler = app.add_handler(
            CallbackQueryHandler(
                self.upload_button_callback, filters=regex("^" + self.callback_data)
            )
        )

    def __str__(self, bot):
        return "#wip"

    async def start(self, from_user_id, filepath, reply, thum, caption, message=""):
        try:
            thum = Path(thum)
            if not thum.is_file():
                thum = None
            async with self.bot.action(from_user_id, "file"):
                await reply.edit("🔺Uploading🔺")
                u_start = time.time()
                if UNLOCK_UNSTABLE and message:
                    s = await message.reply_document(
                        document=filepath,
                        quote=True,
                        thumb=thum,
                        caption=caption,
                        progress=self.progress_for_pyrogram,
                        progress_args=(
                            self.app,
                            f"{CAP_DECO} Uploading {filepath}",
                            reply,
                            u_start,
                        ),
                    )
                else:
                    s = await self.app.send_document(
                        document=filepath,
                        chat_id=from_user_id,
                        force_document=True,
                        thumb=thum,
                        caption=caption,
                        progress=self.progress_for_pyrogram,
                        progress_args=(
                            self.app,
                            "Uploading 👘",
                            reply,
                            u_start,
                        ),
                    )
            self.app.remove_handler(*self.handler)
            return s
        except pyro_errors.BadRequest:
            await reply.edit(f"`Failed {enmoji2()}\nRetrying…`")
            self.app.remove_handler(*self.handler)
            await asyncio.sleep(10)
            upload2 = uploader(self.bot, self.app, self.sender)
            await upload2.start(event.chat_id, loc, e, thum, cap, message)

        except Exception:
            self.app.remove_handler(*self.handler)
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
            return None

    async def progress_for_pyrogram(self, current, total, app, ud_type, message, start):
        now = time.time()
        diff = now - start
        if self.is_cancelled:
            app.stop_transmission()
        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            status = "downloads" + "/status.json"
            if os.path.exists(status):
                with open(status, "r+") as f:
                    statusMsg = json.load(f)
                    if not statusMsg["running"]:
                        app.stop_transmission()
            speed = current / diff
            time_to_completion = time_formatter(int((total - current) / speed))

            progress = "{0}{1} \n<b>Progress:</b> `{2}%`\n".format(
                "".join(
                    [FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]
                ),
                "".join(
                    [
                        UN_FINISHED_PROGRESS_STR
                        for i in range(10 - math.floor(percentage / 10))
                    ]
                ),
                round(percentage, 2),
            )

            tmp = progress + "`{0} of {1}`\n**Speed:** `{2}/s`\n**ETA:** `{3}`\n".format(
                hbs(current),
                hbs(total),
                hbs(speed),
                # elapsed_time if elapsed_time != '' else "0 s",
                time_to_completion if time_to_completion else "0 s",
            )
            try:
                # Create a "Cancel" button
                cancel_button = InlineKeyboardButton(
                    text="Cancel", callback_data=self.callback_data
                )
                # Attach the button to the message with an inline keyboard
                reply_markup = InlineKeyboardMarkup([[cancel_button]])
                if not message.photo:
                    await message.edit_text(
                        text="{}\n {}".format(ud_type, tmp),
                        reply_markup=reply_markup,
                    )
                else:
                    await message.edit_caption(
                        caption="{}\n {}".format(ud_type, tmp),
                        reply_markup=reply_markup,
                    )
            except BaseException:
                pass

    async def upload_button_callback(self, client, callback_query):
        # if callback_query.data == "cancel_upload":
        if (
            str(callback_query.from_user.id) not in OWNER
            and callback_query.from_user.id != self.sender
        ):
            return await callback_query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        self.is_cancelled = True
        self.canceller = callback_query.from_user.id
        await callback_query.answer("Cancelling upload please wait…", show_alert=False)
