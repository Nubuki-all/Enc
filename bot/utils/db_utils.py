from pymongo.errors import ServerSelectionTimeoutError

from bot import asyncio, bot_id
from bot.config import DATABASE_URL as database
from bot.startup.before import ffmpegdb, filterdb, pickle, queuedb, userdb

from .bot_utils import BATCH_QUEUE, QUEUE, TEMP_USERS, list_to_str, sync_to_async
from .local_db_utils import save2db_lcl, save2db_lcl2

# i suck at using database -_-'
# But hey if it works don't touch it
# wanna fix this?
# PRs are welcome

_filter = {"_id": bot_id}


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
        except ServerSelectionTimeoutError as e:
            retries -= 1
            if not retries:
                raise e
            await asyncio.sleep(0.5)


async def save2db2(data=False, db=None):
    if not database:
        return save2db_lcl2() if data is False else None
    if data is False:
        tusers = list_to_str(TEMP_USERS)
        data = pickle.dumps(tusers)
        _update = {"t_users": data}
        await sync_to_async(userdb.update_one, _filter, {"$set": _update}, upsert=True)
        return
    p_data = pickle.dumps(data)
    _update = {db: p_data}
    if db == "ffmpeg":
        await sync_to_async(
            ffmpegdb.update_one, _filter, {"$set": _update}, upsert=True
        )
        return
    if db in ("autoname", "filter"):
        await sync_to_async(
            filterdb.update_one, _filter, {"$set": _update}, upsert=True
        )
        return
