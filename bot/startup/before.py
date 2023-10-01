import pickle

from pymongo import MongoClient

from bot import *
from bot.config import *
from bot.utils.bot_utils import var
from bot.utils.os_utils import file_exists

attrs = dir(var)
globals().update({n: getattr(var, n) for n in attrs if not n.startswith("_")})

uptime = dt.now()
global aria2
aria2 = None


if THUMB:
    os.system(f"wget {THUMB} -O thumb.jpg")

if DL_STUFF:
    for link in DL_STUFF.split(","):
        os.system(f"wget {link.strip()}")

if NO_TEMP_PM:
    TEMP_ONLY_IN_GROUP.append(1)

if not file_exists(ffmpeg_file):
    with open(ffmpeg_file, "w") as file:
        file.write(str(FFMPEG) + "\n")

if not os.path.isdir("downloads/"):
    os.mkdir("downloads/")
if not os.path.isdir("encode/"):
    os.mkdir("encode/")
if not os.path.isdir("temp/"):
    os.mkdir("temp/")
if not os.path.isdir("dump/"):
    os.mkdir("dump/")
if not os.path.isdir("mux/"):
    os.mkdir("mux/")
if not os.path.isdir("thumb/"):
    os.mkdir("thumb/")


if os.path.isdir("/tgenc"):
    DOCKER_DEPLOYMENT.append(1)

if TEMP_USER:
    for t in TEMP_USER.split():
        TEMP_USERS.append(t)


def load_db(_db, _key, var, var_type=None):
    queries = _db.find({"_id": bot_id})
    raw = None
    for query in queries:
        raw = query.get(_key)

    if not raw:
        return
    out = pickle.loads(raw)
    if not out:
        return

    if var_type == "list":
        for item in out.split():
            var.append(item)
    elif var_type == "dict":
        var.update(out)
    else:
        with open(var, "w") as file:
            file.write(out + "\n")


if DATABASE_URL:
    cluster = MongoClient(DATABASE_URL)
    db = cluster[DBNAME]
    queuedb = db["queue"]
    ffmpegdb = db["code"]
    filterdb = db["filter"]
    userdb = db["users"]

    load_db(queuedb, "queue", QUEUE, "dict")
    load_db(userdb, "t_users", TEMP_USERS, "list")
    load_db(ffmpegdb, "ffmpeg", ffmpeg_file)
    load_db(filterdb, "filter", filter_file)
    load_db(filterdb, "autoname", rename_file)

else:
    queuedb = ffmpegdb = filterdb = userdb = None
    if file_exists("local_queue.pkl"):
        with open("local_queue.pkl", "rb") as file:
            local_queue = pickle.load(file)
        QUEUE.update(local_queue)
    if file_exists("t_users.pkl"):
        with open("t_users.pkl", "rb") as file:
            local_users = pickle.load(file)
        for user in local_users:
            TEMP_USERS.append(user)


No_Flood = {}


class EnTimer:
    def __init__(self):
        self.ind_pause = LOCK_ON_STARTUP
        self.time = 0
        self.msg = None

    async def start(self):
        asyncio.create_task(self.timer())

    async def timer(self):
        while True:
            while self.ind_pause or self.time > 0:
                PAUSEFILE.append(0) if not PAUSEFILE else None
                await asyncio.sleep(1)
                print(f"paused for {self.time}")
                if self.time:
                    self.ind_pause = False
                    self.time = self.time - 1
            await asyncio.sleep(1)
            if PAUSEFILE and PAUSEFILE[0] == 0:
                PAUSEFILE.clear()
            if self.msg and not (self.time or self.ind_pause):
                try:
                    for msg in self.msg:
                        await msg.edit(
                            "**Timer ended or cancelled " "and bot has been unpaused.**"
                        )
                except Exception:
                    pass
                self.msg = None

    def new_timer(self, new_time, lmsg=None):
        if isinstance(new_time, int):
            self.time = new_time
            self.msg = lmsg

    def pause_indefinitely(self, lmsg=None):
        self.ind_pause = True
        self.time = 0
        self.msg = lmsg

    def stop_timer(self):
        self.time = 0
        self.ind_pause = False


entime = EnTimer()
