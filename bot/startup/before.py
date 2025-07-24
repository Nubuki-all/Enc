import pickle

from pymongo import MongoClient

from bot import *
from bot.config import _bot, conf
from bot.utils.bot_utils import create_api_token
from bot.utils.local_db_utils import load_local_db
from bot.utils.os_utils import file_exists

LOGS.info("=" * 30)
LOGS.info(f"Python version: {sys.version.split()[0]}")

vmsg = f"Warning: {version_file} is missing!"
if file_exists(version_file):
    with open(version_file, "r") as file:
        ver = file.read().strip()
    vmsg = f"Bot version: {ver}"

LOGS.info(f"Branch: {_bot.repo_branch or 'Unknown!'}")
LOGS.info(vmsg)

if os.path.isdir("/tgenc"):
    _bot.docker_deployed = True
    LOGS.info("Docker: Yes")

LOGS.info("=" * 30)

if conf.THUMB:
    os.system(f"wget {conf.THUMB} -O thumb.jpg")

if conf.CUSTOM_RENAME:
    _bot.custom_rename = conf.CUSTOM_RENAME

if conf.DL_STUFF:
    for link in conf.DL_STUFF.split(","):
        os.system(f"wget {link.strip()}")

if conf.NO_TEMP_PM:
    _bot.temp_only_in_group = True

if conf.REPORT_FAILED:
    _bot.report_failed_dl = True
    _bot.report_failed_enc = True

if conf.REPORT_FAILED_DL:
    _bot.report_failed_dl = True

if conf.REPORT_FAILED_ENC:
    _bot.report_failed_enc = True


ff_files = {
    ffmpeg_file2: conf.FFMPEG2,
    ffmpeg_file3: conf.FFMPEG3,
    ffmpeg_file4: conf.FFMPEG4,
    mux_file: conf.MUX_ARGS,
}

if not file_exists(ffmpeg_file):
    with open(ffmpeg_file, "w") as file:
        file.write(str(conf.FFMPEG) + "\n")

for f_path, value in ff_files.items():
    if not file_exists(f_path) and value:
        with open(f_path, "w") as file:
            file.write(value + "\n")

if not conf.USE_ANILIST:
    Path("NO_PARSE").touch()

if not conf.USE_CAPTION:
    Path("NO_CAPTION").touch()

dirs = (
    "downloads/",
    "dump/",
    "encode/",
    "minfo/",
    "mux/",
    "temp/",
)
for dir_ in dirs:
    if not os.path.isdir(dir_):
        os.mkdir(dir_)


if conf.TEMP_USER:
    for t in conf.TEMP_USER.split():
        if t in conf.OWNER.split():
            continue
        if t not in _bot.temp_users:
            _bot.temp_users.append(t)


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
            if item in conf.OWNER.split():
                continue
            if item not in var:
                var.append(item)
    elif var_type == "dict":
        var.update(out)
    elif var_type == "cust_r":
        _bot.custom_rename = out.strip()
    else:
        with open(var, "w") as file:
            file.write(out + "\n")


if conf.DATABASE_URL:
    cluster = MongoClient(conf.DATABASE_URL)
    db = cluster[conf.DBNAME]
    queuedb = db["queue"]
    ffmpegdb = db["code"]
    filterdb = db["filter"]
    rssdb = db["rss"]
    userdb = db["users"]

    load_db(queuedb, "batches", _bot.batch_queue, "dict")
    load_db(queuedb, "queue", _bot.queue, "dict")
    load_db(userdb, "t_users", _bot.temp_users, "list")
    load_db(filterdb, "autoname", rename_file)
    load_db(filterdb, "cus_rename", None, "cust_r")
    load_db(ffmpegdb, "ffmpeg", ffmpeg_file)
    load_db(filterdb, "filter", filter_file)
    load_db(ffmpegdb, "mux_args", mux_file)
    load_db(rssdb, "rss", _bot.rss_dict, "dict")
    other_ff = [
        ("ffmpeg2", ffmpeg_file2),
        ("ffmpeg3", ffmpeg_file3),
        ("ffmpeg4", ffmpeg_file4),
    ]
    for ff in other_ff:
        load_db(ffmpegdb, ff[0], ff[1])


else:
    queuedb = ffmpegdb = filterdb = rssdb = userdb = None

    load_local_db()

No_Flood = {}

create_api_token()


class EnTimer:
    def __init__(self):
        self.ind_pause = conf.LOCK_ON_STARTUP
        self.time = 0
        self.msg = []

    async def start(self):
        asyncio.create_task(self.timer())

    async def timer(self):
        while True:
            while self.ind_pause or self.time > 0:
                _bot.paused.append(0) if not _bot.paused else None
                await asyncio.sleep(1)
                str_ = "Paused "
                if self.ind_pause:
                    str_ += "Indefinitely!"
                else:
                    str_ += f"for {self.time}"
                print(str_)
                if self.time:
                    self.ind_pause = False
                    self.time = self.time - 1
            await asyncio.sleep(1)
            if _bot.paused and _bot.paused[0] == 0:
                _bot.paused.clear()
            if self.msg and not (self.time or self.ind_pause):
                try:
                    for msg in self.msg:
                        await msg.edit(
                            "**Timer ended or cancelled " "and bot has been unpaused.**"
                        )
                except Exception:
                    pass
                self.msg = []

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
