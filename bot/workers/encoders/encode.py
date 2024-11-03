import asyncio
import os

from bot import Button
from bot.config import conf
from bot.fun.emojis import enmoji
from bot.utils.bot_utils import code, decode
from bot.utils.bot_utils import encode_job as ejob
from bot.utils.bot_utils import get_codec
from bot.utils.log_utils import logger

def_enc_msg = "**Currently Encoding {}:**\n└`{}`\n\n{}**⏳This Might Take A While⏳**"


class Encoder:
    def __init__(self, _id, sender=None, event=None, log=None):
        self.client = None if not event else event.client
        self.enc_id = _id
        self.event = event
        self.log_msg = log
        self.process = None
        self.req_clean = False
        self.sender = sender
        self.log_enc_id = None
        if self.log_msg:
            self.log_enc_id = f"{log.chat_id}:{log.id}"

    def __str__(self):
        return "#WIP"

    async def start(self, cmd):
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        self.process = process
        return process

    async def callback(self, dl, en, event, user, text=def_enc_msg, stime=None):
        try:
            self.req_clean = True
            code(self.process, dl, en, user, stime, self.enc_id)
            out = (os.path.split(en))[1]
            wah = 0
            a_msg = (
                f"**{ejob.get_pending_pos()} Job**\n└`{(await get_codec(ejob.pending()))}`\n\n"
                if ejob.get_pending_pos()
                else str()
            )
            c_button = [Button.inline("Cancel", data=f"skip{wah}")]
            (
                c_button.append(Button.inline("❌ all jobs", data=f"jskip{wah}"))
                if ejob.jobs() > 1
                else None
            )
            e_msg = await event.edit(
                text.format(enmoji(), out, a_msg),
                buttons=[
                    [Button.inline("ℹ️", data=f"pres{wah}")],
                    [
                        Button.inline("Progress", data=f"stats0"),
                        Button.inline("Server-info", data=f"stats1"),
                    ],
                    c_button,
                ],
            )
            if self.log_msg and self.sender:
                code(self.process, dl, en, user, stime, self.log_enc_id)
                sau = (os.path.split(dl))[1]
                e_log = await self.log_msg.edit(
                    f"**User:**\n└[{self.sender.first_name}](tg://user?id={user})\n\n{a_msg}**Currently Encoding:**\n└`{out}`\n\n**Source File:**\n└`{sau}`",
                    buttons=[
                        [Button.inline("ℹ️", data=f"pres{wah}")],
                        [Button.inline("CHECK PROGRESS", data=f"stats2")],
                        [Button.inline("CANCEL PROCESS", data=f"skip{wah}")],
                    ],
                )

        except Exception:
            await logger(Exception)

    async def await_completion(self):
        action = "game" if conf.ALLOW_ACTION is True else "cancel"
        async with self.client.action(self.event.chat_id, action):
            com = await self.process.communicate()
            # while True:
            # if not await is_running(self.process):
            # break
            # await asyncio.sleep(5)
        if self.req_clean:
            decode(self.enc_id, pop=True)
            if self.log_enc_id:
                decode(self.log_enc_id, pop=True)

        return com
