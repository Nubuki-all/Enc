import os
import traceback

from decouple import config
from pathlib import Path
from subprocess import check_output
from subprocess import run as bashrun


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


def update():
    print("Default var for upstream repo & branch will used if none were given!")
    ALWAYS_DEPLOY_LATEST = config(
        "ALWAYS_DEPLOY_LATEST",
        default=False,
        cast=bool)
    AUPR = config("ALWAYS_UPDATE_PY_REQ", default=False, cast=bool)
    UPSTREAM_REPO = config(
        "UPSTREAM_REPO",
        default="https://github.com/Nubuki-all/Enc")
    UPSTREAM_BRANCH = config("UPSTREAM_BRANCH", default="main")

    r_filep = Path("filters/Auto-rename.txt")
    rvars = varsgetter(r_filep)
    update_check = Path("update")
    cmd = (
        f"git switch {UPSTREAM_BRANCH} -q \
        && git pull -q "
        "&& git reset --hard @{u} -q \
        && git clean -df -q"
    )
    cmd2 = f"git init -q \
           && git config --global user.email 117080364+Niffy-the-conqueror@users.noreply.github.com \
           && git config --global user.name Niffy-the-conqueror \
           && git add . \
           && git commit -sm update -q \
           && git remote add origin {UPSTREAM_REPO} \
           && git fetch origin -q \
           && git reset --hard origin/{UPSTREAM_BRANCH} -q \
           && git switch {UPSTREAM_BRANCH} -q"

    if ALWAYS_DEPLOY_LATEST is True or update_check.is_file():
        if UPSTREAM_BRANCH == "main":
            bashrun(["rm -rf .git"], shell=True)
        if os.path.exists('.git') and check_output(
            ["git config --get remote.origin.url"],
                shell=True).decode().strip() == UPSTREAM_REPO:
            update = bashrun([cmd], shell=True)
        else:
            update = bashrun([cmd2], shell=True)
        if AUPR:
            bashrun(["pip3", "install", "-r", "requirements.txt"])
        if update.returncode == 0:
            print('Successfully updated with latest commit from UPSTREAM_REPO')
        else:
            print('Something went wrong while updating,maybe invalid upstream repo?')
        if update_check.is_file():
            os.remove("update")
        varssaver(rvars, r_filep)
    else:
        print("Auto-update is disabled.")


try:
    if __name__ == "__main__":
        update()
except Exception:
    traceback.print_exc()
