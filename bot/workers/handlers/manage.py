import asyncio
import itertools

from bot import caption_file, ffmpeg_file, filter_file, parse_file, rename_file, thumb
from bot.config import FCHANNEL, FFMPEG
from bot.startup.before import DOCKER_DEPLOYMENT as d_docker
from bot.startup.before import entime
from bot.utils.bot_utils import (
    get_aria2,
    get_pause_status,
    get_queue,
    get_var,
    list_to_str,
    split_text,
    time_formatter,
)
from bot.utils.db_utils import save2db, save2db2
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    bc_msg,
    enquoter,
    get_args,
    msg_sleep_delete,
    user_is_owner,
)
from bot.utils.os_utils import file_exists, qclean, re_x, s_remove, updater, x_or_66


async def nuke(event, args, client):
    """Kill bot"""
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        if not d_docker:
            await event.reply("`Exited.`")
            return exit(1)
        rst = await event.reply("`Trying To Nuke ☣️`")
        await asyncio.sleep(1)
        await rst.edit("`☢️ Nuking Please Wait…`")
        x_or_66()
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def restart(event, args, client):
    """Restarts bot."""
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        rst = await event.reply("`Trying To Restart`")
        await asyncio.sleep(1)
        rst_msg = "Restarting Please Wait…"
        rst = await rst.edit(f"`{rst_msg}`")
        message = str(rst.chat_id) + ":" + str(rst.id)
        await enquoter(rst_msg, rst)
        await re_x("restart", message)
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def update2(client, message):
    try:
        if not user_is_owner(message.from_user.id):
            return message.delete()
        upt_mess = "Updating…"
        reply = await message.reply(f"`{upt_mess}`", quote=True)
        await enquoter(upt_mess, reply)
        await updater(reply)
    except Exception:
        await logger(Exception)


async def clean(event, args, client):
    """
    Cleans:
        all files in known working directories
        queued items
        encoding processes
        cached files - if caching is enabled

    Or if 'aria2' is specified;
        clean only files downloaded by aria2
            Not advised if you're currently encoding.
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        aria2 = get_aria2()
        if aria2:
            downloads = aria2.get_downloads()
            await asyncio.sleep(3)
            aria2.remove(downloads, force=True, files=True, clean=True)
        if args and args.casefold() in ("aria", "aria2"):
            return await event.reply("Cleaned up all aria2 files.")
        await event.reply(
            "**Cleared all queued , encoding processes and cached downloads!**"
        )
        get_queue().clear()
        await save2db()
        await qclean()
        return
    except Exception:
        await logger(Exception)


async def allowgroupenc(event, args, client):
    """
    Turns on group encoding on and off;
    Group encoding allows bot to:
        - Download & encode files in group (doesn't affect the /leech command)
        - Set thumbnails in group.

    Required arguments:
        - off/disable (disable group encode)
        - on/enable (enable group encode)
        <All arguments are not case sensitive.>
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    groupenc = get_var("groupenc")

    if not args:
        if groupenc:
            return await event.reply("`Encoding in group is enabled.`")
        else:
            return await event.reply("`Encoding in group is disabled.`")

    if args.casefold() == "off" or args.casefold() == "disable":
        if not groupenc:
            return await event.reply("**Already turned off**")
        groupenc.clear()
        await event.reply("**Turned off Successfully**")
    if args.casefold() == "on" or args.casefold() == "enable":
        if groupenc:
            return await event.reply("**Already turned on**")
        groupenc.append(1)
        yo = await event.reply(
            "**Group Encoding Turned on Successfully**\n__Persists till bot restarts!__"
        )


async def change(event, args, client):
    """
    Changes bot encoding params;

    Requires full shell command with '''{}''' for input and output (use double quotes for better performance)
        - Binary must me be included in argument and must installed locally or in docker
        - Both ffmpeg and handbrake-cli are tested and supported. (Test if others work)
        - ffmpeg two-pass requires specifying input twice which is currently not supported.
            • As a workaround you can create a custom bash script
              check handbrakecli.sh for an example on how to create a custom script then do /set myscript.sh
              for bot to always use your script while encoding.
    Or… path/to/bash_script as arguments.
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        with open(ffmpeg_file, "w") as file:
            file.write(str(args) + "\n")

        await save2db2(args, "ffmpeg")
        await event.reply(f"**Changed FFMPEG Code to**\n\n`{args}`")
    except Exception:
        await logger(Exception)


async def check(event, args, client):
    """
    Get custom encoding params.
    Requires no arguments and any given will be ignored.
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    with open(ffmpeg_file, "r") as file:
        ffmpeg = file.read().rstrip()

    await event.reply(f"**Current ffmpeg Code Is**\n\n`{ffmpeg}`")


async def reffmpeg(event, args, client):
    """
    Reset encoding params.
    Default value to reset to, is contained in .config
    Requires no argument.
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        with open(ffmpeg_file, "w") as file:
            file.write(str(FFMPEG) + "\n")

        await save2db2(FFMPEG, "ffmpeg")
        await event.reply(f"**Changed FFMPEG Code to**\n\n`{FFMPEG}`")
    except Exception:
        await logger(Exception)


async def version2(event, args, client):
    """
    Tag a realese with what numbers you specify:
        - numbers (floats can be specified.)
        - off/disable to turn off
    Sending this command without argument will check for previous version tags and display them.
    """

    if not user_is_owner(event.sender_id):
        return await event.delete()
    version2 = get_var("version2")
    if not args:
        if version2:
            return await event.reply(f"**Current Tag:** `V{version2[0]}`")
        else:
            return await event.reply(
                "__Unfortunately, I can't view what doesn't exist__"
            )

    if args.casefold() == "off" or args.casefold() == "disable":
        if version2:
            tag = version2[0]
            version2.clear()
            return await event.reply(f"**Removed V{tag} tag Successfully!**")
        else:
            return await event.reply("__No tag found__")
    if args.isdigit():
        version2.clear()
        version2.append(args)
        return await event.reply(f"**Added v{args} tag successfully!**")
    else:
        return await event.reply(f"Unknown argument: `{args}`")


async def discap(event, args, client):
    """
    Disable/enable a parsing mechanism:
    Required arguments:
        - anilist
            • on/enable (turns on anilist parsing)
            • off/disable (turns off anilist parsing)
            • ___ (no additional argument) (checks state.)
        - caption (Treats file caption as actual filename)
          *won't work if newlines are detected in caption
            • on/enable (to turn on)
            • off/disable (turn off)
            • ___ (to check state.)
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()

    no = len(args.split(maxsplit=1))
    if no == 1:
        if args.casefold() == "caption":
            if file_exists(caption_file):
                reply = "Parse by caption is disabled."
            else:
                reply = "Parse by caption is enabled."
        elif args.casefold() == "anilist":
            if file_exists(parse_file):
                reply = "__Anilist disabled.__"
            else:
                reply = "__Anilist enabled.__"
        else:
            reply = f"**Unknown argument:** `{args}`"
        return await event.reply(reply)

    arg1, arg2 = args.split(maxsplit=1)
    if arg1.casefold() == "caption":
        if arg2.casefold() in ("on", "enable"):
            if file_exists(caption_file):
                s_remove(caption_file)
                reply = "**Successfully enabled parsing caption as filename**"
            else:
                reply = "__Parsing captions as filename is already enabled__"
        elif arg2.casefold() in ("off", "disable"):
            if file_exists(caption_file):
                reply = "__Parsing captions as filename is already disabled__"
            else:
                with open(caption_file, "w") as file:
                    pass
                reply = "**Successfully disabled parse by caption**"
        else:
            reply = f"Invalid argument for `{arg1}`: `{arg2}`"
        await msg_sleep_delete(event, reply, time=20, del_rep=True)

    elif arg1.casefold() == "anilist":
        if arg2.casefold() in ("on", "enable"):
            if file_exists(parse_file):
                s_remove(parse_file)
                reply = "**Successfully enabled anilist parsing & auto-thumbnail**"
            else:
                reply = "__Anilist has already been enabled__"
        elif arg2.casefold() in ("off", "disable"):
            if file_exists(parse_file):
                reply = "__Anilist is already disabled__"
            else:
                with open(parse_file, "w") as file:
                    pass
                reply = "**Successfully disabled anilist parsing & auto-thumbnail**"
        else:
            reply = f"Invalid argument for `{arg1}`: `{arg2}`"
        await msg_sleep_delete(event, reply, time=20, del_rep=True)

    else:
        await event.reply(
            f"Pray tell thee what does `{args}` mean?\nKindly do /command? -h for how to use this command."
        )


async def auto_rename(event, args, client):
    """
    Ahh yes, the Name filter.
    A tricky command to used indeed
    All arguments are to be separated by '|'

    Required arguments:
        - {anime_name} [Required] (get by clicking i button while downloadingl
        - {replace_name} [Required] (if anime_name is matched use this instead)
        - {replace_cap} [Optional]
            • if not specified caption inherits replace_name.
            • if '0', a digit, is passed, filter is ignored for caption.
            • if '1', a digit, is passed, it is the same as not specifying.
            • if anything else is specified it uses that as captain name instead.
        Both {replace_name} and {replace_cap} also accept '00', a double digit
        which essentially disables all fiter and anilist parsing
        for the anime_name.

    How to use:
        Example : /name My Little Puppy|MLP|0
            - All files with My Little Puppy get renamed to MLP.
            - Caption is ignored and normal settings apply.
        For more examples see Auto-rename.txt.
    """
    fail_msg = (
        "failed…\n**Try:**\n/name " "`(Add_name_to_check_for|Add_name_to_replace_with)`"
    )
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        if "|" not in args:
            return await event.reply(fail_msg)
        with open(rename_file, "r") as file:
            r_file = file.read().strip().rstrip("\n")
        rslt = args.split("|")
        for __check in r_file.split("\n"):
            if __check.split("|")[0].casefold() == rslt[0].casefold():
                return await event.reply(
                    "__Already added.__\n" "To edit, remove and add again."
                )
        with open(rename_file, "w") as file:
            file.write(r_file + "\n" + str(args))
        n_no = len(r_file.split("\n"))
        with open(rename_file, "r") as file:
            r_file = file.read().strip()
        await save2db2(r_file, "autoname")
        await event.reply(
            f"**NO:** `{n_no}`\n\n"
            f"**Check for: **`{rslt[0]}`\n"
            f"**Replace with: ** `{rslt[1]}`"
        )
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def v_auto_rename(event, args, client):
    """View all name filters."""
    if not user_is_owner(event.sender_id):
        return await event.delete()
    if not file_exists(rename_file):
        return event.reply("`Nothing but a void.`")
    with open(rename_file, "r") as file:
        r_file = file.read().rstrip()
    if not r_file:
        return event.reply("`Nothing but a void.`")
    reply = list_to_str(
        r_file.split("\n"),
        "\n\n",
        0,
        True,
    )

    replies = await split_text(reply)
    for i, reply in zip(itertools.count(1), replies):
        await event.reply(f"**Here you go #{i}:**\n\n{reply}")


async def del_auto_rename(event, args, client):
    """
    Unlike it's adding counterpart, removing is quite easy simply;
    Do /vname and copy the exact filter you want to remove or its number:
    Then as argument, pass:
        - one of the filter listed out
            (might fail if there are whitelines)
        - the number stated next to it

    *command requires the above argument
    """
    fail_msg = (
        f"failed\n**Try:**\n/delname "
        f"`(Add_name_to_check_for|Add_name_to_replace_with)`"
    )
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        if "|" not in args:
            if not args.isdigit():
                return await event.reply(fail_msg)
        with open(rename_file, "r") as file:
            r_file = file.read().strip()
        if args.isdigit():
            dat = r_file.split("\n")
            if ((args := int(args)) + 1) > len(dat):
                return await event.reply(
                    "__Not found check /vname and pass appropriate number__"
                )
            rslt = dat[args].split("|")
            dat.pop(args)
            r_file = list_to_str(dat, "\n")
        else:
            dat = r_file.split("\n")
            if args not in dat:
                return await event.reply("__Not found check with__ /vname")
            dat.remove(args)
            r_file = list_to_str(dat, "\n")
            rslt = args.split("|")

        with open(rename_file, "w") as file:
            file.write(str(r_file))
        await save2db2(r_file, "autoname")
        return await event.reply(
            f"**Will no longer check for: **`{rslt[0]}`\n"
            f"**and replace with: ** `{rslt[1]}`"
        )
    except Exception:
        await logger(Exception)


async def filter(event, args, client):
    """
    Another filter command. (Not to be confused with namefilter)
    Unlike namefilter this targets the file_name and is universal.
    Requires the Following arguments:
        -f {what to remove} removes the specified string from all filenames
            can be used with multiple items each separated/delimited with '|'
        -t {filetag}
            • … <str> (force tag all file as your input without the '[]')
            • disable <str> (to disable)
            • auto <str> (tag files as usual) (default behaviour if argument is not specified)
        -c {captag}
            • … <str> (tag all captions as …)
            • disable <str> (to disable)
            • auto <str> (tag captions as usual) (default if not specified.)
            • to add more info add '{auto}' to argument.
              that way both the original caption tag
              and the added one is displayed.
        if arguments contains spaces put them in quotes
        else they'll be missing

    Note: Each usage of this command will overwrite the previous even if the argument wasn't specified
    so always specify the argument you want to use each time you send the command.
    *must specify an argument.

    Related commands:
        - /vfilter, /delfilter
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        arg = get_args("-f", "-t", "-c", to_parse=args)
        if not arg.f and not arg.t and not arg.c:
            return await event.reply(f"`{filter.__doc__}`")

        f = arg.f if arg.f else "Not my problem."
        t = arg.t if arg.t else "auto"
        c = arg.c if arg.c else "auto"
        temp = f"{f}\n{t}\n{c}"
        with open(filter_file, "w") as file:
            file.write(temp)
        await save2db2(temp, "filter")
        await event.reply(
            "**Changed filters Successfully!**\n" "`To view send /vfilter`."
        )
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def vfilter(event, args, client):
    """View currently added filter."""
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        if not file_exists(filter_file):
            return await event.reply("`❌ No Filters Found!`")
        with open("filter.txt", "r") as file:
            fil = file.read().strip("\n").split("\n")
        fil1, fil2, fil3 = fil
        await event.reply(
            "Bot Will Automatically:\n\n"
            f"**Remove:-** `{fil1}`\n"
            f"**Tag Files as:-** `{fil2}`\n"
            f"**Tag caption as:-** `{fil3}`"
        )
    except Exception:
        await event.reply("An Error Occurred.")
        await logger(Exception)


async def rmfilter(event, args, client):
    """Delete previously added filter"""
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        if not file_exists(filter_file):
            await event.reply("❌ No Filters Found To Delete")
            return
        s_remove(filter_file)
        await save2db2(None, "filter")
        await event.reply("`Filters Deleted!`")
    except Exception:
        await logger(Exception)


async def save_thumb(event, args, client):
    """Save/replace default thumbnail"""
    if not user_is_owner(event.sender_id):
        return
    if not event.photo:
        return
    if not event.is_private and not get_var("groupenc"):
        rply = (
            "`Ignoring…`\nTurn on encoding videos in groups with "
            "`/groupenc on` to enable setting thumbnails in groups.\n"
            "__This message shall self-destruct in 20 seconds.__"
        )
        await msg_sleep_delete(event, rply, time=20)
    s_remove(thumb)
    await event.client.download_media(event.media, file=thumb)
    await event.reply("**Thumbnail Saved Successfully.**")


async def pause(event, args, client):
    """
    Pause bot;
    Prevent bot from encoding for a specified duration.
    muxing and renaming are not paused.
    Arguments:
        - A number
            • for instance: /pause 900 to pause for 900 seconds or;
              /pause 0 to pause indefinitely till you cancel with /pause off"
        - off/disable (To unpause)
        - no argument; (To check state)
    """
    if not user_is_owner(event.sender_id):
        return await event.delete()
    try:
        if not args:
            if get_pause_status() == 0:
                reply = "**Parse Status:** `Bot is currently paused.`"
            else:
                reply = "**Pause Status:** `Bot is not paused.`"
            return await event.reply(reply)
        elif args.casefold() in ("disable", "off"):
            if get_pause_status() == 0:
                entime.stop_timer()
                reply = "**Pausing Cancelled**"
            else:
                reply = "**Bot was not paused**"
            return await event.reply(reply)
        elif not args.isdigit():
            return await event.reply("No clue as to what " f"`{args}` means.")
        args = int(args)
        if args == 0:
            reply = "**Bot has been paused indefinitely.**"
        else:
            reply = f"`Bot has been paused for {time_formatter(args)}`"
        event2 = await event.reply(reply)
        l_msg = await bc_msg(reply, event.sender_id, [event2])
        if not args:
            entime.pause_indefinitely(l_msg)
        else:
            entime.new_timer(args, l_msg)
    except Exception:
        await logger(Exception)


async def fc_forward(msg):
    """Forwards replied message to FCHANNEL"""
    try:
        if not FCHANNEL:
            return await msg.reply("`FCHANNEL var not set.`")
        if not msg.reply_to_message:
            return await msg.reply("`Reply with a message to forward to FCHANNEL`")
        f_msg = msg.reply_to_message
        await f_msg.copy(chat_id=FCHANNEL)
        await msg.reply("`Forwarded succesfully.`")
    except Exception:
        await logger(Exception)
