from bot import *
from bot.config import _bot, conf
from bot.fun.emojis import enhearts, enmoji, enmoji2
from bot.utils.bot_utils import (
    code,
    decode,
    get_aria2,
    hbs,
    replace_proxy,
    sync_to_async,
    time_formatter,
    value_check,
)
from bot.utils.log_utils import log, logger
from bot.utils.os_utils import parse_dl, s_remove

from .dl_helpers import (
    get_files_from_torrent,
    get_qbclient,
    rm_leech_file,
    rm_torrent_file,
    rm_torrent_tag,
)


class Downloader:
    def __init__(
        self,
        sender=123456,
        lc=None,
        _id=None,
        uri=False,
        dl_info=False,
        folder="downloads/",
        qbit=None,
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
        self.aria2 = get_aria2()
        self.path = None
        self.qb = None
        self.qbit = qbit
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
            if self.qbit:
                return await self.start3(dl, file, message, e, select)
            elif self.uri:
                return await self.start2(dl, file, message, e)
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

    async def start2(self, dl, file, message, e):
        try:
            await self.log_download()
            self.time = ttt = time.time()
            await asyncio.sleep(3)
            if not self.aria2:
                self.download_error = "E404: Aria2 is currently not available."
                raise Exception(self.download_error)
            downloads = await sync_to_async(
                self.aria2.add, self.uri, {"dir": f"{os.getcwd()}/{self.dl_folder}"}
            )
            self.uri_gid = downloads[0].gid
            download = await sync_to_async(self.aria2.get_download, self.uri_gid)
            while True:
                if message:
                    download = await self.progress_for_aria2(download, ttt, e)
                else:
                    download = await self.progress_for_aria2(
                        downloads[0].gid, ttt, e, silent=True
                    )
                if not download:
                    break
                if download.is_complete:
                    break
            await self.wait()
            self.un_register()
            return download

        except Exception:
            self.un_register()
            await logger(Exception)
            return None

    async def start3(self, dl, file, message, e, s):
        try:
            await self.log_download()
            await asyncio.sleep(3)
            self.qb = await sync_to_async(get_qbclient)
            self.message = e
            result = await sync_to_async(
                self.qb.torrents_add,
                self.uri,
                save_path=f"{os.getcwd()}/{self.dl_folder}",
                seeding_time_limit=0,
                is_paused=False,
                tags=self.id,
            )
            self.time = ttt = time.time()
            if result.lower() == "ok.":
                tor_info = await sync_to_async(self.qb.torrents_info, tag=self.id)
                if len(tor_info) == 0:
                    while True:
                        tor_info = await sync_to_async(
                            self.qb.torrents_info, tag=self.id
                        )
                        if len(tor_info) > 0:
                            break
                        elif time.time() - ttt >= 120:
                            self.download_error = "Failed to add torrent…"
                            raise Exception(self.download_error)
            else:
                self.download_error = (
                    "This Torrent already added or unsupported/invalid link/file"
                )
                raise Exception(self.download_error)
            if tor_info[0].state == "metaDL":
                st = time.time()
                await e.edit_text("`Getting torrent's metadata. Please wait…`")
                while True:
                    tor_info = await sync_to_async(self.qb.torrents.info, tag=self.id)
                    if tor_info[0].state != "metaDL":
                        break
                    elif time.time() - st >= 360:
                        self.download_error = "Failed to get metadata…"
                        raise Exception(self.download_error)
            if tor_info[0].state == "error":
                self.download_error = "An unknown error occurred."
                raise Exception(self.download_error)
            self.uri_gid = tor_info[0].hash
            await sync_to_async(self.qb.torrents_pause, torrent_hashes=self.uri_gid)
            file_list = await get_files_from_torrent(self.uri_gid, self.id)
            name = file_list[0] if len(file_list) == 1 else None
            self.file_name = (
                file_list[s] if s is not None else (name or tor_info[0].name)
            )
            self.path = self.dl_folder + self.file_name

            length = len(file_list)
            x = str()
            if s is not None:
                if s > (length - 1):
                    self.download_error = "qbittorrent: file_id not found."
                    raise Exception(self.download_error)
                for i in range(length):
                    if i != s:
                        x += str(i) + "|"
                x = x.strip("|")
            (
                await sync_to_async(
                    self.qb.torrents_file_priority,
                    torrent_hash=self.uri_gid,
                    file_ids=x,
                    priority=0,
                )
                if x
                else None
            )
            await sync_to_async(self.qb.torrents_resume, torrent_hashes=self.uri_gid)
            while True:
                download = await self.progress_for_qbit()
                if not download:
                    break
                if download.state == "pausedUP":
                    break
            await self.wait()
            self.un_register()
            return download

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

    async def progress_for_aria2(self, download, start, message, silent=False):
        try:
            download = download.live
            if download.followed_by_ids:
                gid = download.followed_by_ids[0]
                try:
                    download = await sync_to_async(self.aria2.get_download, gid)
                except Exception:
                    log(Exception)
            if download.status == "error" or self.is_cancelled:
                if download.status == "error":
                    self.download_error = (
                        "E" + download.error_code + ": " + download.error_message
                    )
                await sync_to_async(download.remove, force=True, files=True)
                if download.following_id:
                    download = await sync_to_async(
                        self.aria2.get_download, download.following_id
                    )
                    await sync_to_async(download.remove, force=True, files=True)
                return None

            ud_type = "`Download Pending…`"
            if not download.name.endswith(".torrent"):
                self.file_name = download.name
                self.path = self.dl_folder + self.file_name
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

            progress = "```\n{0}{1}```\n<b>Progress:</b> `{2}%`\n".format(
                "".join([fin_str for i in range(math.floor(download.progress / 10))]),
                "".join(
                    [
                        self.unfin_str
                        for i in range(10 - math.floor(download.progress / 10))
                    ]
                ),
                round(download.progress, 2),
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
            dl = await self.progress_for_aria2(download, start, message, silent)
            return dl

        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            await asyncio.sleep(2)
            dl = await self.progress_for_aria2(download, start, message, silent)
            return dl

        except Exception:
            await logger(Exception)
            await self.clean_download()
            return None

    async def progress_for_qbit(self):
        try:
            download = await sync_to_async(self.qb.torrents_info, tag=self.id)
            download = download[0]
            if self.is_cancelled:
                await self.clean_download()
                return
            ud_type = "`..................`"
            if download.state == "pausedUP":
                return download
            elif download.state == "checkingResumeData":
                ud_type = "`Starting Download…`"
            elif download.state == "stalledDL":
                ud_type = "`Download stalled…`"
            elif download.state == "downloading":
                file_name = (os.path.split(self.file_name))[1]
                ud_type = f"**Downloading:**\n`{file_name}`"
                ud_type += "\n**via:** Torrent."
            total = download.size
            current = download.completed
            speed = download.dlspeed
            remaining = total - current
            start = self.time
            time_to_completion = download.eta
            now = time.time()
            diff = now - start
            fin_str = enhearts()
            d_progress = (current / total) * 100

            progress = "```\n{0}{1}```\n<b>Progress:</b> `{2}%`\n".format(
                "".join([fin_str for i in range(math.floor(d_progress / 10))]),
                "".join(
                    [self.unfin_str for i in range(10 - math.floor(d_progress / 10))]
                ),
                round(d_progress, 2),
            )
            tmp = (
                progress
                + "`{0} of {1}`\n**Speed:** `{2}/s`\n**Remains:** `{3}`\n**ETA:** `{4}`\n**Elapsed:** `{5}`\n".format(
                    value_check(hbs(current)),
                    value_check(hbs(total)),
                    value_check(hbs(speed)),
                    value_check(hbs(remaining)),
                    time_formatter(time_to_completion) if time_to_completion else "0 s",
                    time_formatter(diff),
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
            except BaseException:
                await logger(BaseException)
            if not self.message.photo:
                self.message = await self.message.edit_text(
                    text=dsp,
                    reply_markup=reply_markup,
                )
            else:
                self.message = await self.message.edit_caption(
                    caption=dsp,
                    reply_markup=reply_markup,
                )

            await asyncio.sleep(10)
            return download
        except pyro_errors.BadRequest:
            await asyncio.sleep(10)
            dl = await self.progress_for_qbit()
            return dl

        except pyro_errors.FloodWait as e:
            await asyncio.sleep(e.value)
            await asyncio.sleep(2)
            dl = await self.progress_for_qbit()
            return dl

        except Exception as e:
            self.download_error = str(e)
            await logger(Exception)
            await self.clean_download()
            return None

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
            if self.qbit:
                await rm_torrent_file(self.uri_gid, qb=self.qb)
                await rm_torrent_tag(self.id, qb=self.qb)
            elif self.uri:
                rm_leech_file(self.uri_gid)
            else:
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
