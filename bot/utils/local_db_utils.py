import pickle

from bot import local_qdb, local_udb

from .bot_utils import QUEUE, TEMP_USERS, list_to_str
from .os_utils import file_exists


def load_local_db():
    if file_exists(local_qdb):
        with open(local_qdb, "rb") as file:
            local_queue = pickle.load(file)
        QUEUE.update(local_queue)

    if file_exists(local_udb):
        with open(local_udb, "rb") as file:
            local_users = pickle.load(file)
        for user in local_users:
            if user not in TEMP_USERS:
                TEMP_USERS.append(user)


def save2db_lcl():
    with open(local_qdb, "wb") as file:
        pickle.dump(QUEUE, file)


def save2db_lcl2():
    with open(local_udb, "wb") as file:
        pickle.dump(list_to_str(TEMP_USERS), file)
