import os
from decouple import config
from pathlib import Path
from subprocess import run as bashrun

try:
    print("Default var for upstream repo & branch will used if none were given!")
    UPSTREAM_REPO = config("UPSTREAM_REPO", default="")
    UPSTREAM_BRANCH = config("UPSTREAM_BRANCH", default="")
    ALWAYS_DEPLOY_LATEST = config(
        "ALWAYS_DEPLOY_LATEST",
        default=False,
        cast=bool)
except Exception:
    print("Environment vars Missing")
    traceback.print_exc()


def varsgetter(files):
    evars = ""
    if files.is_file():
        with open(files, "r") as file:
            evars = file.read().rstrip()
            file.close()
    return evars


def varssaver(evars, files):
    if evars:
        file = open(files, "w")
        file.write(str(evars) + "\n")
        file.close()


envp = Path(".env")
ffmpegp = Path("ffmpeg.txt")
filterp = Path("filter.txt")
envars = varsgetter(envp)
ffmpegs = varsgetter(ffmpegp)
filters = varsgetter(filterp)
update_check = Path("update")

try:
    if ALWAYS_DEPLOY_LATEST is True or update_check.is_file():
        if not UPSTREAM_REPO:
            UPSTREAM_REPO = "https://github.com/Nubuki-all/Tg-coder"
        if not UPSTREAM_BRANCH:
            UPSTREAM_BRANCH = "main"
        if os.path.exists('.git'):
            bashrun(["rm", "-rf", ".git"])
        update = bashrun([f"git init -q \
                       && git config --global user.email 117080364+Niffy-the-conqueror@users.noreply.github.com \
                       && git config --global user.name Niffy-the-conqueror \
                       && git add . \
                       && git commit -sm update -q \
                       && git remote add origin {UPSTREAM_REPO} \
                       && git fetch origin -q \
                       && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)
        if update.returncode == 0:
            print('Successfully updated with latest commit from UPSTREAM_REPO')
            if update_check.is_file():
                os.remove("update")
            varssaver(envars, envp)
            varssaver(ffmpegs, ffmpegp)
            varssaver(filters, filterp)
        else:
            print('Something went wrong while updating,maybe invalid upstream repo?')
except Exception:
    traceback.print_exc()
