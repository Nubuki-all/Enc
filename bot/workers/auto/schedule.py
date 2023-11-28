from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from tzlocal import get_localzone


def addjob(delay: int, function, id="0", name="RSS"):
    scheduler.add_job(
        function,
        trigger=IntervalTrigger(seconds=delay),
        id=id,
        name=name,
        misfire_grace_time=15,
        max_instances=1,
        next_run_time=datetime.now() + timedelta(seconds=20),
        replace_existing=True,
    )


scheduler = AsyncIOScheduler(timezone=str(get_localzone()))
