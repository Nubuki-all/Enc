from bot import *
from bot.config import _bot, conf
from bot.fun.emojis import enhearts, enmoji, enmoji2
from bot.utils.bot_utils import code, decode, hbs, replace_proxy, time_formatter
from bot.utils.log_utils import log, logger
from bot.utils.os_utils import parse_dl, s_remove


class Downloader:
    def __init__(
        self,
        sender=123456,
        lc=None,
        _id=None,
        uri=False,
        dl_info=False,
        folder="downloads/",
    ):
        self.sender = int(sender)
        self.callback_data = "cancel_download"
        self.is_cancelled = False
        self.canceller = None
        self.dl_info = dl_info
        self.download_error = None
        self.file_name = None
        self.message = None
        self.dl_folder = folder
        self.id = _id
        self.uri = replace_proxy(uri)
        self.uri_gid = None
        self.lc = lc
        self.lm = None
        self.log_id = None
        self._sender = None
        self.time = None
        self.path = None
        self.unfin_str = conf.UN_FINISHED_PROGRESS_STR
        self.display_dl_info = _bot.display_additional_dl_info
        if conf.PAUSE_ON_DL_INFO:
            self.pause_on_dl_info = True
        else:
            self.pause_on_dl_info = False
        if self.dl_info:
            self.callback_data_i = "dl_info"
            self.callback_data_b = "back"

    def __str__(self):
        return "#wip"

    def gen_buttons(self):
        # Create a "Cancel" button
        cancel_button = InlineKeyboardButton(
            text=f"{enmoji()} Cancel Download", callback_data=self.callback_data
        )
        if self.dl_info:
            # Create an "info" button
            info_button = InlineKeyboardButton(
                text="ℹ️", callback_data=self.callback_data_i
            )
            # Create a "more" button
            more_button = InlineKeyboardButton(
                text="More…",
                callback_data=f"more 0",
            )
            # create "back" button
            back_button = InlineKeyboardButton(
                text="↩️", callback_data=self.callback_data_b
            )
        else:
            info_button, more_button, back_button = None, None, None
        return info_button, more_button, back_button, cancel_button

    async def log_download(self):
        if self.lc:
            try:
                cancel_button = InlineKeyboardButton(
                    text=f"{enmoji()} CANCEL DOWNLOAD", callback_data=self.callback_data
                )
                more_button = InlineKeyboardButton(
                    text="ℹ️",
                    callback_data=f"more 1",
                )
                reply_markup = InlineKeyboardMarkup([[more_button], [cancel_button]])
                dl_info = await parse_dl(self.file_name)
                msg = "Currently downloading a video"
                if self.uri:
                    msg += " from a link"
                message = await pyro.get_messages(self.lc.chat_id, self.lc.id)
                self._sender = self._sender or await pyro.get_users(self.sender)
                log = await message.edit(
                    f"`{msg} sent by` {self._sender.mention(style='md')}\n" + dl_info,
                    reply_markup=reply_markup,
                )
                self.lm = message
            except Exception:
                await logger(Exception)

    async def start(self, dl, file, message="", e="", select=None):
        try:
            self.file_name = dl
            self.register()
            await self.log_download()
            if self.dl_folder:
                self.path = dl = self.dl_folder + dl
            if message:
                self.time = ttt = time.time()
                media_type = str(message.media)
                if media_type == "MessageMediaType.DOCUMENT":
                    media_mssg = "`Downloading a file…`"
                else:
                    media_mssg = "`Downloading a video…`"
                download_task = await pyro.download_media(
                    message=message,
                    file_name=dl,
                    progress=self.progress_for_pyrogram,
                    progress_args=(pyro, media_mssg, e, ttt),
                )
            else:
                download_task = await pyro.download_media(
                    message=file,
                    file_name=dl,
                )
            await self.wait()
            if self.is_cancelled:
                await self.clean_download()
            self.un_register()
            return download_task

        except pyro_errors.BadRequest:
            await reply.edit(f"`Failed {enmoji2()}\nRetrying in 10 seconds…`")
            await asyncio.sleep(10)
            dl_task = await self.start(dl, file, message, e)
            return dl_task

        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            await reply.edit(
                f"`Failed: FloodWait error {enmoji2()}\nRetrying in 10 seconds…`"
            )
            await asyncio.sleep(10)
            dl_task = await self.start(dl, file, message, e)
            return dl_task

        except Exception:
            self.un_register()
            await logger(Exception)
            return None

    async def progress_for_pyrogram(self, current, total, app, ud_type, message, start):
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

            progress = "```\n{0}{1}```\n<b>Progress:</b> `{2}%`\n".format(
                "".join([fin_str for i in range(math.floor(percentage / 10))]),
                "".join(
                    [self.unfin_str for i in range(10 - math.floor(percentage / 10))]
                ),
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
                # Attach the button to the message with an inline keyboard
                reply_markup = []
                # file_name = self.file_name.split("/")[-1]
                dl_info = await parse_dl(self.file_name)
                (
                    info_button,
                    more_button,
                    back_button,
                    cancel_button,
                ) = self.gen_buttons()
                if not self.dl_info:
                    reply_markup.append([cancel_button])
                    dsp = "{}\n{}".format(ud_type, tmp)
                elif not self.display_dl_info:
                    reply_markup.extend(([info_button], [cancel_button]))
                    dsp = "{}\n{}".format(ud_type, tmp)
                else:
                    reply_markup.extend(([more_button], [back_button], [cancel_button]))
                    dsp = dl_info
                reply_markup = InlineKeyboardMarkup(reply_markup)
                if not message.photo:
                    self.message = await message.edit_text(
                        text=dsp,
                        reply_markup=reply_markup,
                    )
                else:
                    self.message = await message.edit_caption(
                        caption=dsp,
                        reply_markup=reply_markup,
                    )
            except pyro_errors.FloodWait as e:
                await asyncio.sleep(e.value)
            except BaseException:
                await logger(Exception)
                # debug

    def register(self):
        try:
            code(self, index=self.id)
            if self.lc:
                self.log_id = f"{self.lc.chat_id}:{self.lc.id}"
                code(self, index=self.log_id)
        except Exception:
            log(Exception)

    def un_register(self):
        if self.dl_info:
            return
        try:
            decode(self.id, pop=True)
            if self.log_id:
                decode(self.log_id, pop=True)
        except Exception:
            log(Exception)

    async def clean_download(self):
        try:
            s_remove(self.path)
        except Exception:
            log(Exception)

    async def wait(self):
        if (
            self.message
            and self.display_dl_info
            and self.pause_on_dl_info
            and self.dl_info
        ):
            msg = "been completed." if not self.is_cancelled else "been cancelled!"
            msg = "ran into errors!" if self.download_error else msg
            reply_markup = []
            (
                info_button,
                more_button,
                back_button,
                cancel_button,
            ) = self.gen_buttons()
            reply_markup.extend(([more_button], [back_button]))
            reply_markup = InlineKeyboardMarkup(reply_markup)
            await self.message.edit(
                self.message.text.markdown + f"\n\n`Download has {msg}\n"
                "To continue click back.`",
                reply_markup=reply_markup,
            )
        while self.dl_info and self.display_dl_info and self.pause_on_dl_info:
            await asyncio.sleep(5)
