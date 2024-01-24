import asyncio

from feedparser import parse as feedparse

from bot import pyro, rss_dict_lock
from bot.config import _bot, conf
from bot.workers.auto.schedule import addjob, scheduler
from bot.workers.handlers.queue import enleech, enleech2

from .bot_utils import RSS_DICT as rss_dict
from .bot_utils import check_cmds, get_html
from .db_utils import save2db2
from .log_utils import log
from .msg_utils import send_rss


async def rss_monitor():
    """
    An asynchronous function to get rss links
    """
    if not (_bot.sas and _bot.sqs):
        await asyncio.sleep(10)
        if _bot.sas and _bot.sqs:
            return
        log(
            e="RSS scheduler has been paused since a download service is not responding…"
        )
        if _bot.started:
            scheduler.pause()
        return
    if not conf.RSS_CHAT:
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
            html = await get_html(data["link"])
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
            feed_list = []
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
                feed_list.append(feed_msg)
                feed_count += 1
            for feed_msg in reversed(feed_list):
                event = await send_rss(feed_msg, data["chat"])
                if event and data.get("direct", True):
                    await fake_event_handler(event)
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
        log(e="No active rss feed\nRss Monitor has been paused!")


async def fake_event_handler(event):
    """
    Passes the rss message to the bot as a new event.
        Args:
            event (telethon.events): _description_
    """
    command, args = event.text.split(maxsplit=1)
    if not check_cmds(command, "/l", "/ql", "/qbleech", "/leech"):
        return
    if check_cmds(command, "/l", "/leech"):
        asyncio.create_task(enleech(event, args, pyro, True))
    elif check_cmds(command, "/ql", "/qbleech"):
        asyncio.create_task(enleech2(event, args, pyro, True))
    await asyncio.sleep(3)


def schedule_rss():
    addjob(conf.RSS_DELAY, rss_monitor)


schedule_rss()
scheduler.start()
