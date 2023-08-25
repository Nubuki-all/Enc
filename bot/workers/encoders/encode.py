import asyncio

from bot import ALLOW_ACTION, Button
from bot.utils.bot_utils import code, decode
from bot.utils.log_utils import logger

def_enc_msg = "`Encoding File(s)…` \n**⏳This Might Take A While⏳**"


class Encoder:
    def __init__(self, _id, sender=None, event=None, log=None):
        self.client = None if not event else event.client
        self.enc_id = _id
        self.event = event
        self.log_msg = log
        self.process = None
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

    async def callback(self, dl, en, event, user, text=def_enc_msg):
        try:
            code(self.process, dl, en, user, self.enc_id)
            wah = 0
            e_msg = await event.edit(
                text,
                buttons=[
                    [Button.inline("ℹ️", data=f"pres{wah}")],
                    [Button.inline("Progress & Server-info", data=f"stats{wah}")],
                    [Button.inline("Cancel", data=f"skip{wah}")],
                ],
            )
            if self.log_msg and self.sender:
                code(self.process, dl, en, user, self.log_enc_id)
                e_log = await self.log_msg.edit(
                    f"[{self.sender.first_name}](tg://user?id={user}) `Is Currently Encoding a Video…`",
                    buttons=[
                        [Button.inline("ℹ️", data=f"pres{wah}")],
                        [Button.inline("CHECK PROGRESS", data=f"stats{wah}")],
                        [Button.inline("CANCEL PROCESS", data=f"skip{wah}")],
                    ],
                )

        except Exception:
            await logger(Exception)

    async def await_completion(self):
        action = "game" if ALLOW_ACTION is True else "cancel"
        async with self.client.action(self.event.chat_id, action):
            com = await self.process.communicate()
            # while True:
            # if not await is_running(self.process):
            # break
            # await asyncio.sleep(5)
        decode(self.enc_id, pop=True)
        if self.log_enc_id:
            decode(self.log_enc_id, pop=True)

        return com
