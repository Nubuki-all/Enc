from pymongo.errors import ServerSelectionTimeoutError

from bot import asyncio, bot_id
from bot.config import conf
from bot.startup.before import ffmpegdb, filterdb, pickle, queuedb, rssdb, userdb

from .bot_utils import BATCH_QUEUE, QUEUE, TEMP_USERS, list_to_str, sync_to_async
from .local_db_utils import save2db_lcl, save2db_lcl2

# i suck at using database -_-'
# But hey if it works don't touch it
# wanna fix this?
# PRs are welcome

_filter = {"_id": bot_id}

database = conf.DATABASE_URL


async def save2db(db="queue", retries=3):
    if not database:
        return save2db_lcl()
    d = {"queue": QUEUE, "batches": BATCH_QUEUE}
    data = pickle.dumps(d.get(db))
    _update = {db: data}
    while retries:
        try:
            await sync_to_async(
                queuedb.update_one, _filter, {"$set": _update}, upsert=True
            )
            break
        except ServerSelectionTimeoutError as e:
            retries -= 1
            if not retries:
                raise e
            await asyncio.sleep(0.5)


async def save2db2(data: dict | str = False, db: str = None):
    if not database:
        if data is False or db == "rss":
            await save2db_lcl2(db)
        return
    if data is False:
        tusers = list_to_str(TEMP_USERS)
        data = pickle.dumps(tusers)
        _update = {"t_users": data}
        await sync_to_async(userdb.update_one, _filter, {"$set": _update}, upsert=True)
        return
    p_data = pickle.dumps(data)
    _update = {db: p_data}
    if db in ("ffmpeg", "mux_args"):
        await sync_to_async(
            ffmpegdb.update_one, _filter, {"$set": _update}, upsert=True
        )
        return
    if db in ("autoname", "filter"):
        await sync_to_async(
            filterdb.update_one, _filter, {"$set": _update}, upsert=True
        )
        return
    if db == "rss":
        await sync_to_async(rssdb.update_one, _filter, {"$set": _update}, upsert=True)
        return
