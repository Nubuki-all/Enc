import asyncio

from aiohttp import ClientSession
from feedparser import parse as feedparse

from bot import pyro, rss_dict_lock
from bot.config import CMD_SUFFIX as suffix
from bot.config import RSS_DIRECT as rss_direct
from bot.utils.bot_utils import RSS_DICT as rss_dict
from bot.utils.db_utils import save2db2
from bot.utils.log_utils import log
from bot.utils.msg_utils import event_handler, send_rss
from bot.utils.rss_utils import scheduler
from bot.workers.handlers.queue import enleech, enleech2


async def rss_monitor():
    """
    An asynchronous function to get rss links
    """
    if not "RSS_CHAT":
        log(e="RSS_CHAT not added! Shutting down rss scheduler...")
        scheduler.shutdown(wait=False)
        return
    if len(rss_dict) == 0:
        scheduler.pause()
        return
    all_paused = True
    for title, data in list(rss_dict.items()):
        try:
            if data["paused"]:
                continue
            async with ClientSession(trust_env=True) as session:
                async with session.get(data["link"]) as res:
                    html = await res.text()
            rss_d = feedparse(html)
            try:
                last_link = rss_d.entries[0]["links"][1]["href"]
            except IndexError:
                last_link = rss_d.entries[0]["link"]
            finally:
                all_paused = False
            last_title = rss_d.entries[0]["title"]
            if data["last_feed"] == last_link or data["last_title"] == last_title:
                continue
            feed_count = 0
            while True:
                try:
                    item_title = rss_d.entries[feed_count]["title"]
                    try:
                        url = rss_d.entries[feed_count]["links"][1]["href"]
                    except IndexError:
                        url = rss_d.entries[feed_count]["link"]
                    if data["last_feed"] == url or data["last_title"] == item_title:
                        break
                except IndexError:
                    log(
                        e=f"Reached Max index no. {feed_count} for this feed: {title}. Maybe you need to use less RSS_DELAY to not miss some torrents"
                    )
                    break
                parse = True
                for flist in data["inf"]:
                    if all(x not in item_title.lower() for x in flist):
                        parse = False
                        feed_count += 1
                        break
                for flist in data["exf"]:
                    if any(x in item_title.lower() for x in flist):
                        parse = False
                        feed_count += 1
                        break
                if not parse:
                    continue
                cmd = data["command"].split(maxsplit=1)
                cmd.insert(1, url)
                feed_msg = " ".join(cmd)
                if not feed_msg.startswith("/"):
                    feed_msg = f"/{feed_msg}"
                event = await send_rss(feed_msg)
                if event and rss_direct:
                    await fake_event(event)
                feed_count += 1
                await asyncio.sleep(1)
            async with rss_dict_lock:
                rss_dict[title].update(
                    {"last_feed": last_link, "last_title": last_title}
                )
            await save2db2(rss_dict, "rss")
            log(e=f"Feed Name: {title}")
            log(e=f"Last item: {last_link}")
        except Exception as e:
            log(e=f"{e} - Feed Name: {title} - Feed Link: {data['link']}")
            continue
    if all_paused:
        scheduler.pause()


def check_cmds(command: str, *matches: str):
    def check_cmd(command: str, match: str):
        match += suffix
        c = command.split(match, maxsplit=1)
        return len(c) == 2 and not c[1]

    for match in matches:
        if check_cmd(command, match):
            return True
    return False


async def fake_event(event):
    """
    Passes the rss message to the bot as a new event.
        Args:
            event (telethon.events): _description_
    """
    command = event.text.split(maxsplit=1)[0]
    if not check_cmds(command, "/l", "/ql", "/qbleech", "/leech"):
        return
    if check_cmds(command, "/l", "/leech"):
        asyncio.create_task(event_handler(event, enleech, pyro))
    elif check_cmds(command, "/ql", "/qbleech"):
        asyncio.create_task(event_handler(event, enleech2, pyro))
    await asyncio.sleep(3)
