import os
from decouple import config
from subprocess import run as bashrun

try:
    print("Default var for upstream repo & branch will used if none were given!")
    UPSTREAM_REPO = config("UPSTREAM_REPO", default="")
    UPSTREAM_BRANCH = config("UPSTREAM_BRANCH", default="")
except Exception:
    print("Environment vars Missing")
    traceback.print_exc()
try:
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
    else:
        print('Something went wrong while updating,maybe invalid upstream repo?')
except Exception:
    traceback.print_exc()
