import uuid

from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from .funcn import *
from .util import parse_dl, qparse


class uploader:
    def __init__(self, sender=123456):
        self.sender = int(sender)
        self.callback_data = "cancel_upload" + str(uuid.uuid4())
        self.is_cancelled = False
        self.canceller = None
        self.handler = app.add_handler(
            CallbackQueryHandler(
                self.upload_button_callback, filters=regex("^" + self.callback_data)
            )
        )

    def __str__(self):
        return "#wip"

    async def start(self, from_user_id, filepath, reply, thum, caption, message=""):
        try:
            if thum:
                thum = Path(thum)
                if not thum.is_file():
                    thum = None
            async with bot.action(from_user_id, "file"):
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
                            app,
                            f"**{CAP_DECO} Uploading:** `{filepath}…`\n",
                            reply,
                            u_start,
                        ),
                    )
                else:
                    s = await app.send_document(
                        document=filepath,
                        chat_id=from_user_id,
                        force_document=True,
                        thumb=thum,
                        caption=caption,
                        progress=self.progress_for_pyrogram,
                        progress_args=(
                            app,
                            "Uploading 👘",
                            reply,
                            u_start,
                        ),
                    )
            app.remove_handler(*self.handler)
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
            app.remove_handler(*self.handler)
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
            return None

    async def progress_for_pyrogram(self, current, total, app, ud_type, message, start):
        fin_str = enhearts()
        unfin_str = UN_FINISHED_PROGRESS_STR
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
                "".join([fin_str for i in range(math.floor(percentage / 10))]),
                "".join([unfin_str for i in range(10 - math.floor(percentage / 10))]),
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


class downloader:
    def __init__(self, sender=123456, lc=None, uri=False, dl_info=False, folder="downloads"):
        self.sender = sender
        self.sender_is_id = False
        self.callback_data = "cancel_download" + str(uuid.uuid4())
        self.is_cancelled = False
        self.canceller = None
        self.dl_info = dl_info
        self.download_error = None
        self.file_name = None
        self.dl_folder = folder
        self.uri = uri
        self.uri_gid = None
        self.lc = lc
        self.lm = None
        self.handler = app.add_handler(
            CallbackQueryHandler(
                self.download_button_callback, filters=regex("^" + self.callback_data)
            )
        )
        self.aria2 = ARIA2[0]
        DISPLAY_DOWNLOAD = DISPLAY_DOWNLOAD
        if str(sender).isdigit():
            self.sender_is_id = True
            self.sender = int(sender)
        if self.dl_info:
            self.callback_data_i = "dl_info" + str(uuid.uuid4())
            self.callback_data_b = "back" + str(uuid.uuid4())
            self.handler_i = app.add_handler(
                CallbackQueryHandler(
                    self.dl_info, filters=regex("^" + self.callback_data_i)))
            self.handler_b = app.add_handler(
                CallbackQueryHandler(
                    self.back, filters=regex("^" + self.callback_data_b)))


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
                text="ℹ️", callback_data= self.callback_data_i
            )
            # Create a "more" button
            more_button = InlineKeyboardButton(
                text="More…", callback_data=f"more {code(self.file_name)}"
            )
            # create "back" button
            back_button = InlineKeyboardButton(
                text="↩️", callback_data= self.callback_data_b
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
                    text="ℹ️", callback_data=f"more {code(self.file_name)}"
                )
                reply_markup = InlineKeyboardMarkup([[more_button], [cancel_button]])
                dl_info = await parse_dl(self.file_name)
                msg = "Currently downloading a video"
                if self.uri:
                    msg += " from a link"
                message = await app.get_messages(self.lc.chat_id, self.lc.id)
                log = await message.edit(
                    f"`{msg} sent by` {self.sender.mention(style='md')}\n" + dl_info,
                    reply_markup=reply_markup,
                )
                self.lm = message
            except Exception:
                ers = traceback.format_exc()
                LOGS.info(ers)
                await channel_log(ers)

    async def start(self, dl, file, message="", e=""):
        try:
            self.file_name = dl
            if self.uri:
                return await self.start2(dl, file, message, e)
            await self.log_download()
            if message:
                ttt = time.time()
                media_type = str(message.media)
                if media_type == "MessageMediaType.DOCUMENT":
                    media_mssg = "`Downloading a file…`\n"
                else:
                    media_mssg = "`Downloading a video…`\n"
                download_task = await app.download_media(
                    message=message,
                    file_name=dl,
                    progress=self.progress_for_pyrogram,
                    progress_args=(app, media_mssg, e, ttt),
                )
            else:
                download_task = await app.download_media(
                    message=file,
                    file_name=dl,
                )
            try:
                if self.is_cancelled:
                    os.remove(dl)
            except Exception:
                pass
            app.remove_handler(*self.handler)
            if self.dl_info:
                app.remove_handler(*self.handler_i)
                app.remove_handler(*self.handler_b)
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
            app.remove_handler(*self.handler)
            if self.dl_info:
                app.remove_handler(*self.handler_i)
                app.remove_handler(*self.handler_b)
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
            return None

    async def start2(self, dl, file, message, e):
        try:
            await self.log_download()
            ttt = time.time()
            await asyncio.sleep(3)
            downloads = self.aria2.add(self.uri, {"dir": f"{os.getcwd()}/{self.dl_folder}"})
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
            app.remove_handler(*self.handler)
            if self.dl_info:
                app.remove_handler(*self.handler_i)
                app.remove_handler(*self.handler_b)
            return download
        except Exception:
            app.remove_handler(*self.handler)
            if self.dl_info:
                app.remove_handler(*self.handler_i)
                app.remove_handler(*self.handler_b)
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
            return None

    async def progress_for_pyrogram(self, current, total, app, ud_type, message, start):
        fin_str = enhearts()
        unfin_str = UN_FINISHED_PROGRESS_STR
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
                "".join([fin_str for i in range(math.floor(percentage / 10))]),
                "".join([unfin_str for i in range(10 - math.floor(percentage / 10))]),
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
                elif not DISPLAY_DOWNLOAD:
                    reply_markup.extend(([info_button], [cancel_button]))
                    dsp = "{}\n{}".format(ud_type, tmp)
                else:
                    reply_markup.extend(([more_button], [back_button], [cancel_button]))
                    dsp = dl_info
                reply_markup = InlineKeyboardMarkup(reply_markup)
                if not message.photo:
                    await message.edit_text(
                        text=dsp,
                        reply_markup=reply_markup,
                    )
                else:
                    await message.edit_caption(
                        caption=dsp,
                        reply_markup=reply_markup,
                    )
            except BaseException:
                LOGS.info(traceback.format_exc())

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
                        "E" + download.error_code + " :" + download.error_message
                    )
                download.remove(force=True, files=True)
                if download.following_id:
                    download = self.aria2.get_download(download.following_id)
                    download.remove(force=True, files=True)
                return None

            ud_type = "`Download Pending…`"
            if not download.name.endswith(".torrent"):
                ud_type = f"Downloading `{download.name}`"
                if download.is_torrent:
                    ud_type += " via torrent."
            remaining_size = download.total_length - download.completed_length
            total = download.total_length
            current = download.completed_length
            speed = download.download_speed
            # time_to_completion = download.eta
            time_to_completion = ""
            now = time.time()
            diff = now - start
            fin_str = enhearts()
            unfin_str = UN_FINISHED_PROGRESS_STR

            if download.completed_length and download.download_speed:
                time_to_completion = time_formatter(
                    int(
                        (download.total_length - download.completed_length)
                        / download.download_speed
                    )
                )

            progress = "{0}{1} \n<b>Progress:</b> `{2}%`\n".format(
                "".join([fin_str for i in range(math.floor(download.progress / 10))]),
                "".join(
                    [unfin_str for i in range(10 - math.floor(download.progress / 10))]
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
                elif not DISPLAY_DOWNLOAD:
                    reply_markup.extend(([info_button], [cancel_button]))
                    dsp = "{}\n{}".format(ud_type, tmp)
                else:
                    reply_markup.extend(([more_button], [back_button], [cancel_button]))
                    dsp = dl_info
                reply_markup = InlineKeyboardMarkup(reply_markup)
            except BaseException:
                pass
            if not message.photo:
                await message.edit_text(
                    text=dsp,
                    reply_markup=reply_markup,
                )
            else:
                await message.edit_caption(
                    caption=dsp,
                    reply_markup=reply_markup,
                )

            await asyncio.sleep(11)
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
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
            return None

    async def download_button_callback(self, client, callback_query):
        try:
            if self.sender_is_id:
                user = self.sender
            else:
                user = self.sender.id
            if (
                str(callback_query.from_user.id) not in OWNER
                and callback_query.from_user.id != user
            ):
                return await callback_query.answer(
                    "You're not allowed to do this!", show_alert=False
                )
            self.is_cancelled = True
            self.canceller = await app.get_users(callback_query.from_user.id)
            await callback_query.answer(
                "Cancelling download please wait…", show_alert=False
            )
        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)
            await channel_log(ers)

    async def dl_info(client, query):
        try:
            await query.answer()
            DISPLAY_DOWNLOAD.append(1)
        except Exception:
            er = traceback.format_exc()
            LOGS.info(er)
            await channel_log(er)
    
    
    async def back(client, query):
        try:
            await query.answer()
            DISPLAY_DOWNLOAD.clear()
        except Exception:
            er = traceback.format_exc()
            LOGS.info(er)
            await channel_log(er)


async def dl_stat(client, query):
    try:
        data = query.data.split()
        dl = decode(data[1])
        if not dl:
            raise IndexError("No data!")
        dl_check = Path(dl)
        if dl_check.is_file():
            dls = dl
        else:
            dls = f"{dl}.temp"
        ov = hbs(int(Path(dls).stat().st_size))
        name = dl.split("/")[1]
        input = (name[:45] + "…") if len(name) > 45 else name
        q = await qparse(name)
        ans = f"📥 Downloading:\n{input}\n\n⭕ Current Size:\n{ov}\n\n\n{enmoji()}:\n{q}"
        await query.answer(ans, cache_time=0, show_alert=True)
    except IndexError:
        ansa = "Oops! data of this button was lost,\n most probably due to restart.\nAnd as such the outdated message will be removed…"
        await query.answer(ansa, cache_time=0)
        await asyncio.sleep(5)
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            ers = traceback.format_exc()
            LOGS.info("[DEBUG] -dl_stat- " + ers)
        await query.message.delete()
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        await channel_log(ers)
        ans = "Yikes 😬"
        await query.answer(ans, cache_time=0, show_alert=True)


app.add_handler(CallbackQueryHandler(dl_stat, filters=regex("^more")))
