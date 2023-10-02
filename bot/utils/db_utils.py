from bot import bot_id
from bot.config import DATABASE_URL as database
from bot.startup.before import ffmpegdb, filterdb, pickle, queuedb, userdb

from .bot_utils import QUEUE, TEMP_USERS, list_to_str
from .local_db_utils import save2db_lcl, save2db_lcl2

# i suck at using database -_-'
# But hey if it works don't touch it
# wanna fix this?
# PRs are welcome

_filter = {"_id": bot_id}


async def save2db():
    if not database:
        return save2db_lcl()
    data = pickle.dumps(QUEUE)
    _update = {"queue": data}
    queuedb.update_one(_filter, {"$set": _update}, upsert=True)


async def save2db2(data=False, db=None):
    if not database:
        return save2db_lcl2() if data is False else None
    if data is False:
        tusers = list_to_str(TEMP_USERS)
        data = pickle.dumps(tusers)
        _update = {"t_users": data}
        userdb.update_one(_filter, {"$set": _update}, upsert=True)
        return
    p_data = pickle.dumps(data)
    _update = {db: p_data}
    if db == "ffmpeg":
        ffmpegdb.update_one(_filter, {"$set": _update}, upsert=True)
        return
    if db in ("autoname", "filter"):
        filterdb.update_one(_filter, {"$set": _update}, upsert=True)
        return
