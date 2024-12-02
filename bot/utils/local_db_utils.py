import pickle

from bot import _bot, local_cdb, local_qdb, local_qdb2, local_rdb, local_udb

from .bot_utils import list_to_str
from .os_utils import file_exists


def load_local_db():
    if file_exists(local_qdb):
        with open(local_qdb, "rb") as file:
            local_queue = pickle.load(file)
        _bot.queue.update(local_queue)

    if file_exists(local_qdb2):
        with open(local_qdb2, "rb") as file:
            local_queue = pickle.load(file)
        _bot.batch_queue.update(local_queue)

    if file_exists(local_rdb):
        with open(local_rdb, "rb") as file:
            local_dict = pickle.load(file)
        _bot.rss_dict.update(local_dict)

    if file_exists(local_udb):
        with open(local_udb, "rb") as file:
            local_users = pickle.load(file)
        for user in local_users.split():
            if user not in _bot.temp_users:
                _bot.temp_users.append(user)

    if file_exists(local_cdb):
        with open(local_cdb, "rb") as file:
            local_format = pickle.load(file)
        _bot.custom_rename = local_format


def save2db_lcl():
    with open(local_qdb, "wb") as file:
        pickle.dump(_bot.queue, file)
    with open(local_qdb2, "wb") as file:
        pickle.dump(_bot.batch_queue, file)


def save2db_lcl2(db):
    if db is None:
        with open(local_udb, "wb") as file:
            pickle.dump(list_to_str(_bot.temp_users), file)
    elif db == "rss":
        with open(local_rdb, "wb") as file:
            pickle.dump(_bot.rss_dict, file)
    elif db == "cus_rename":
        with open(local_cdb, "wb") as file:
            pickle.dump(_bot.custom_rename, file)
