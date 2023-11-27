from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from tzlocal import get_localzone

from bot.config import RSS_DELAY as rss_delay
from bot.workers.auto.rss import rss_monitor


def addjob(delay: int):
    scheduler.add_job(
        rss_monitor,
        trigger=IntervalTrigger(seconds=delay),
        id="0",
        name="RSS",
        misfire_grace_time=15,
        max_instances=1,
        next_run_time=datetime.now() + timedelta(seconds=20),
        replace_existing=True,
    )


scheduler = AsyncIOScheduler(timezone=str(get_localzone()))

addjob(rss_delay)
scheduler.start()
