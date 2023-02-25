import os
from decouple import config
from pathlib import Path
from subprocess import run as bashrun

try:
    print("Default var for upstream repo & branch will used if none were given!")
    UPSTREAM_REPO = config("UPSTREAM_REPO", default="")
    UPSTREAM_BRANCH = config("UPSTREAM_BRANCH", default="")
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

try:
    if UPSTREAM_REPO:
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
            varssaver(envars, envp)
            varssaver(ffmpegs, ffmpegp)
            varssaver(filters, filterp)
        else:
            print('Something went wrong while updating,maybe invalid upstream repo?')
except Exception:
    traceback.print_exc()
