from bot import *
from bot.fun.emojis import enhearts, enmoji, enmoji2
from bot.fun.stuff import dbar, ubar, vbar
from bot.utils.bot_utils import DISPLAY_DOWNLOAD
from bot.utils.bot_utils import UN_FINISHED_PROGRESS_STR as unfin_str
from bot.utils.bot_utils import (
    code,
    decode,
    get_aria2,
    hbs,
    replace_proxy,
    time_formatter,
    value_check,
)
from bot.utils.log_utils import logger
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
        self.sender = sender
        self.sender_is_id = False
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
        self.time = None
        self.aria2 = get_aria2()
        if DISPLAY_DOWNLOAD:
            self.display_dl_info = True
        else:
            self.display_dl_info = False
        if PAUSE_ON_DL_INFO:
            self.pause_on_dl_info = True
        else:
            self.pause_on_dl_info = False
        if str(sender).isdigit():
            self.sender_is_id = True
            self.sender = int(sender)
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
                log = await message.edit(
                    f"`{msg} sent by` {self.sender.mention(style='md')}\n" + dl_info,
                    reply_markup=reply_markup,
                )
                self.lm = message
            except Exception:
                await logger(Exception)

    async def start(self, dl, file, message="", e=""):
        try:
            self.file_name = dl
            code(self, index=self.id)
            if self.uri:
                return await self.start2(dl, file, message, e)
            await self.log_download()
            if self.dl_folder:
                dl = self.dl_folder + dl
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
                s_remove(dl)
            decode(self.id, pop=True)
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
            decode(self.id, pop=True)
            await logger(Exception)
            return None

    async def start2(self, dl, file, message, e):
        try:
            await self.log_download()
            self.time = ttt = time.time()
            await asyncio.sleep(3)
            if not self.aria2:
                self.download_error = "E404: Aria2 is currently not available."
                raise Exception(self.download_error)
            downloads = self.aria2.add(
                self.uri, {"dir": f"{os.getcwd()}/{self.dl_folder}"}
            )
            self.uri_gid = downloads[0].gid
            while True:
                if message:
                    download = await self.progress_for_aria2(downloads[0].gid, ttt, e)
                else:
                    download = await self.progress_for_aria2(
                        downloads[0].gid, ttt, e, silent=True
                    )
                if not download:
                    break
                if download.is_complete:
                    break
            await self.wait()
            decode(self.id, pop=True)
            return download

        except Exception:
            decode(self.id, pop=True)
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

            progress = (
                f"{ubar}\n{vbar} "
                "{0}{1} {2}\n<b>Progress:</b> `{3}%`\n".format(
                    "".join([fin_str for i in range(math.floor(percentage / 10))]),
                    "".join(
                        [unfin_str for i in range(10 - math.floor(percentage / 10))]
                    ),
                    f"{vbar}\n{dbar}",
                    round(percentage, 2),
                )
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

    async def progress_for_aria2(self, gid, start, message, silent=False):
        try:
            download = self.aria2.get_download(gid)
            download = download.live
            if download.followed_by_ids:
                gid = download.followed_by_ids[0]
            download = self.aria2.get_download(gid)
            if download.status == "error" or self.is_cancelled:
                if download.status == "error":
                    self.download_error = (
                        "E" + download.error_code + ": " + download.error_message
                    )
                download.remove(force=True, files=True)
                if download.following_id:
                    download = self.aria2.get_download(download.following_id)
                    download.remove(force=True, files=True)
                return None

            ud_type = "`Download Pending…`"
            if not download.name.endswith(".torrent"):
                self.file_name = download.name
                ud_type = f"**Downloading:**\n`{download.name}`"
                ud_type += "\n**via:** "
                if download.is_torrent:
                    ud_type += "Torrent."
                else:
                    ud_type += "Direct Link."
            remaining_size = download.total_length - download.completed_length
            total = download.total_length
            current = download.completed_length
            speed = download.download_speed
            # time_to_completion = download.eta
            time_to_completion = ""
            now = time.time()
            diff = now - start
            fin_str = enhearts()

            if download.completed_length and download.download_speed:
                time_to_completion = time_formatter(
                    int(
                        (download.total_length - download.completed_length)
                        / download.download_speed
                    )
                )

            progress = (
                f"{ubar}\n{vbar} "
                "{0}{1} {2}\n<b>Progress:</b> `{3}%`\n".format(
                    "".join(
                        [fin_str for i in range(math.floor(download.progress / 10))]
                    ),
                    "".join(
                        [
                            unfin_str
                            for i in range(10 - math.floor(download.progress / 10))
                        ]
                    ),
                    f"{vbar}\n{dbar}",
                    round(download.progress, 2),
                )
            )
            tmp = (
                progress
                + "`{0} of {1}`\n**Speed:** `{2}/s`\n**Remains:** `{3}`\n**ETA:** `{4}`\n**Elapsed:** `{5}`\n".format(
                    value_check(hbs(current)),
                    value_check(hbs(total)),
                    value_check(hbs(speed)),
                    value_check(hbs(remaining_size)),
                    # elapsed_time if elapsed_time != '' else "0 s",
                    # download.eta if len(str(download.eta)) < 30 else "0 s",
                    time_to_completion if time_to_completion else "0 s",
                    time_formatter(diff),
                )
            )
            if silent:
                await asyncio.sleep(10)
                return download
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
            except BaseException:
                await logger(BaseException)
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

            await asyncio.sleep(10)
            return download
        except pyro_errors.BadRequest:
            await asyncio.sleep(10)
            dl = await self.progress_for_aria2(gid, start, message, silent)
            return dl

        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            await asyncio.sleep(2)
            dl = await self.progress_for_aria2(gid, start, message, silent)
            return dl

        except Exception:
            await logger(Exception)
            return None

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
