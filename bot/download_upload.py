from .funcn import *


class uploader:
    def __init__(self, bot, app):
        self.bot = bot
        self.app = app
        self.is_cancelled = False
        app.add_handler(CallbackQueryHandler(self.button_callback))

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
                        progress_args=(self.app, "Uploading 👘", reply, u_start),
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
            return s
        except Exception:
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)

    async def progress_for_pyrogram(self, current, total, app, ud_type, message, start):
        now = time.time()
        diff = now - start
        # debug
        LOGS.info(self.is_cancelled)
        if self.is_cancelled:
            app.stop_transmission()
            await message.edit_text("`Uploading Cancelled.`")
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
                    text="Cancel", callback_data="cancel_upload"
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

    # @app.on_callback_query()
    async def button_callback(self, callback_query):
        # debug
        LOGS.info("function is called?")
        if callback_query.data == "cancel_upload":
            LOGS.info("data matches")
            self.is_cancelled = True
            LOGS.info(f"is set to cancelled: {self.is_cancelled}")
