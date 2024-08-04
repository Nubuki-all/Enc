from bot import *
from bot.config import conf
from bot.fun.emojis import enhearts, enmoji, enmoji2
from bot.utils.bot_utils import code, decode, hbs, time_formatter
from bot.utils.log_utils import logger
from bot.utils.os_utils import file_exists


class Uploader:
    def __init__(self, sender=123456, _id=None):
        self.sender = int(sender)
        self.callback_data = "cancel_upload"
        self.is_cancelled = False
        self.id = _id
        self.canceller = None
        self.time = None
        self.unfin_str = conf.UN_FINISHED_PROGRESS_STR

    def __str__(self):
        return "#wip"

    async def start(self, from_user_id, filepath, reply, thum, caption, message=""):
        try:
            if not thum or not (thum and file_exists(thum)):
                if not file_exists(thumb):
                    thum = None
                else:
                    thum = thumb
            code(self, index=self.id)
            fm = f"**From folder:** `{os.path.split(filepath)[0]}`"
            fm += f"\n**File:** `{os.path.split(filepath)[1]}`"
            async with tele.action(from_user_id, "file"):
                await reply.edit("🔺Uploading🔺")
                self.time = u_start = time.time()
                s = await message.reply_document(
                    document=filepath,
                    quote=True,
                    thumb=thum,
                    caption=caption,
                    progress=self.progress_for_pyrogram,
                    progress_args=(
                        pyro,
                        f"**{conf.CAP_DECO} Uploading…**",
                        reply,
                        u_start,
                        fm,
                    ),
                )
            decode(self.id, pop=True)
            return s
        except pyro_errors.BadRequest:
            await reply.edit(f"`Failed {enmoji2()}\nRetrying in 10 seconds…`")
            await asyncio.sleep(10)
            s = await self.start(from_user_id, filepath, reply, thum, caption, message)
            return s

        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            await reply.edit(
                f"`Failed: FloodWait error {enmoji2()}\nRetrying in 10 seconds…`"
            )
            await asyncio.sleep(10)
            s = await self.start(from_user_id, filepath, reply, thum, caption, message)
            return s

        except Exception:
            decode(self.id, pop=True)
            await logger(Exception)

    async def progress_for_pyrogram(
        self, current, total, app, ud_type, message, start, file_info
    ):
        fin_str = enhearts()
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
            elapsed_time = time_formatter(diff)
            speed = current / diff
            time_to_completion = time_formatter(int((total - current) / speed))

            progress = "```\n{0}{1}```\n{2}\n<b>Progress:</b> `{3}%`\n".format(
                "".join([fin_str for i in range(math.floor(percentage / 10))]),
                "".join(
                    [self.unfin_str for i in range(10 - math.floor(percentage / 10))]
                ),
                file_info,
                round(percentage, 2),
            )

            tmp = (
                progress
                + "`{0} of {1}`\n**Speed:** `{2}/s`\n**ETA:** `{3}`\n**Elapsed:** `{4}`\n".format(
                    hbs(current),
                    hbs(total),
                    hbs(speed),
                    time_to_completion if time_to_completion else "0 s",
                    elapsed_time if elapsed_time != "" else "0 s",
                )
            )
            try:
                # Create a "Cancel" button
                cancel_button = InlineKeyboardButton(
                    text=f"{enmoji()} Cancel", callback_data=self.callback_data
                )
                # Attach the button to the message with an inline keyboard
                reply_markup = InlineKeyboardMarkup([[cancel_button]])
                if not message.photo:
                    await message.edit_text(
                        text="{}\n{}".format(ud_type, tmp),
                        reply_markup=reply_markup,
                    )
                else:
                    await message.edit_caption(
                        caption="{}\n{}".format(ud_type, tmp),
                        reply_markup=reply_markup,
                    )
            except pyro_errors.FloodWait as e:
                await asyncio.sleep(e.value)
            except BaseException:
                pass
