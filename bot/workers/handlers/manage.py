import asyncio
import itertools

from feedparser import parse as feedparse

from bot import (
    caption_file,
    ffmpeg_file,
    ffmpeg_file2,
    ffmpeg_file3,
    ffmpeg_file4,
    filter_file,
    mux_file,
    parse_file,
    rename_file,
    rss_dict_lock,
    thumb,
)
from bot.config import _bot, conf
from bot.startup.before import entime
from bot.utils.bot_utils import encode_job as ejob
from bot.utils.bot_utils import (
    get_aria2,
    get_bqueue,
    get_html,
    get_pause_status,
    get_queue,
    get_var,
    list_to_str,
    split_text,
    string_escape,
    sync_to_async,
    time_formatter,
)
from bot.utils.db_utils import save2db, save2db2
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    avoid_flood,
    bc_msg,
    enquoter,
    event_handler,
    get_args,
    msg_sleep_delete,
    try_delete,
    user_is_owner,
)
from bot.utils.os_utils import (
    file_exists,
    kill_process,
    qclean,
    re_x,
    s_remove,
    updater,
    x_or_66,
)
from bot.utils.rss_utils import schedule_rss, scheduler
from bot.workers.downloaders.dl_helpers import get_qbclient


async def nuke(event, args, client):
    """Stop/Nuke bot."""
    if not user_is_owner(event.sender_id):
        return await msg_sleep_delete(event, "😂", time=5, del_rep=True)
    try:
        if not _bot.docker_deployed:
            await event.reply("`Exited.`")
            await clean_all_qb()
            await qclean()
            return exit(1)
        rst = await event.reply("`Trying To Nuke ☣️`")
        await asyncio.sleep(1)
        await rst.edit("`☢️ Nuked!`")
        await clean_all_qb()
        x_or_66()
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def restart(event, args, client):
    """Restarts bot. (To avoid issues use /update instead.)"""
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    try:
        rst = await event.reply("`Trying To Restart`")
        await asyncio.sleep(1)
        rst_msg = "Restarting Please Wait…"
        rst = await rst.edit(f"`{rst_msg}`")
        message = str(rst.chat_id) + ":" + str(rst.id)
        await enquoter(rst_msg, rst)
        try:
            await clean_all_qb()
        except Exception:
            pass
        await re_x("restart", message)
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def update2(client, message):
    """Fetches latest update for bot"""
    try:
        if not user_is_owner(message.from_user.id):
            return try_delete(message)
        upt_mess = "Updating…"
        reply = await message.reply(f"`{upt_mess}`", quote=True)
        await enquoter(upt_mess, reply)
        try:
            await clean_all_qb()
        except Exception:
            pass
        await updater(reply)
    except Exception:
        await logger(Exception)


async def clean_all_aria2():
    aria2 = get_aria2()
    if aria2:
        downloads = aria2.get_downloads()
        await asyncio.sleep(3)
        aria2.remove(downloads, force=True, files=True, clean=True)


async def clean_all_qb():
    qb = await sync_to_async(get_qbclient)
    for torrent in await sync_to_async(qb.torrents_info):
        print(f"{torrent.hash[-6:]}: {torrent.name} ({torrent.state})")
        await sync_to_async(
            qb.torrents_delete, delete_files=True, torrent_hashes=torrent.hash
        )


async def clean(event, args, client):
    """
    Cleans:
        all files in known working directories
        queued items
        encoding processes
        cached files - if caching is enabled

    Or:
    if 'aria2' is specified;
        cleans only files downloaded by aria2
            Not advised if you're currently encoding.
    if 'ffmpeg' is specified;
        kills all ffmpeg processes
            Not advised if you're running multiple ffmpeg process.
    if 'queue' is specified;
        clears all queued items.
            Not advised if encoding as already started, use /clear all instead
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    try:
        if args and args.casefold() == "ffmpeg":
            kill_process("ffmpeg")
            return await event.reply("Killed all ffmpeg processes.")
        if args and args.casefold() == "queue":
            get_bqueue().clear()
            get_queue().clear()
            await save2db()
            await save2db("batches")
            return await event.reply("Cleared ALL items on queue.")

        if args and args.casefold() in ("aria", "aria2"):
            await clean_all_aria2()
            return await event.reply("Cleaned up all aria2 files.")
        if args and args.casefold() in ("qbit", "qbittorrent", "qb"):
            await clean_all_qb()
            return await event.reply("Cleaned up all qbit fies.")
        await event.reply(
            "**Cleared all queued , encoding processes and cached downloads!**"
        )
        get_bqueue().clear()
        get_queue().clear()
        await save2db()
        await save2db("batches")
        await qclean()
        await clean_all_aria2()
        try:
            await clean_all_qb()
        except Exception:
            pass
        return
    except Exception as e:
        await logger(Exception)
        await event.reply(f"```\n{str(e)}\n```")


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


async def set_mux_args(event, args, client):
    """
    Set, reset or disable muxing after transcoding.
    Arguments:
        ffmpeg params without the (-i input & output)
            Do not pass encoding params, only map, metadata, dispositions are allowed.
        or:

        reset
            to reset the mux_args to same parameter in env.
            - if env is not set it is disabled.
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    try:
        if args.casefold() == "reset":
            if not conf.MUX_ARGS:
                if file_exists(mux_file):
                    s_remove(mux_file)
                    await save2db2(None, "mux_args")
                    return await event.reply("**Successfully unset mux_args**")
                else:
                    return await event.reply(
                        f"**Muxing argument was not set; Therefore cannot {args}!**"
                    )
            args = conf.MUX_ARGS
        with open(mux_file, "w") as file:
            file.write(str(args) + "\n")
        await save2db2(args, "mux_args")
        await event.reply(
            f"<pre>\n<code class='language-Changed mux_args to:'>{args}</code>\n</pre>",
            parse_mode="html",
        )
    except Exception:
        await logger(Exception)


async def get_mux_args(event, args, client):
    """
    Get currently set mux_args
    Requires no arguments and any given will be ignored.
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    if not file_exists(mux_file):
        return await avoid_flood(event.reply, "__mux_args not set.__")
    with open(mux_file, "r") as file:
        m = file.read().rstrip("\n").rstrip()

    await event.reply(
        f"<pre>\n<code class='language-Current mux_args:'>{m}</code>\n</pre>",
        parse_mode="html",
    )


async def change(event, args, client):
    """
    Changes bot encoding params;

    Requires full shell command with '''{}''' for input and output (use double quotes for better performance)
        - Binary name must me be included in argument and must installed locally or in docker
        - Both ffmpeg and handbrake-cli are tested and supported. (Test if others work)
        - ffmpeg two-pass requires specifying input twice which is currently not supported.
            • As a workaround you can create a custom bash script
              check handbrakecli.sh for an example on how to create a custom script then do /set myscript.sh
              for bot to always use your script while encoding.
    Or… path/to/bash_script as arguments.
    To set for FFMPEG2(or 3 or 4), add -2 or -3 and so on, before the shell command for encoding.
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    try:
        if args.startswith("-2"):
            args = (args.split("-2", maxsplit=1)[1]).strip()
            file = ffmpeg_file2
            db = "ffmpeg2"
            s = "2"
        elif args.startswith("-3"):
            args = (args.split("-3", maxsplit=1)[1]).strip()
            file = ffmpeg_file3
            db = "ffmpeg3"
            s = "3"
        elif args.startswith("-4"):
            args = (args.split("-4", maxsplit=1)[1]).strip()
            file = ffmpeg_file4
            db = "ffmpeg4"
            s = "4"
        else:
            file = ffmpeg_file
            db = "ffmpeg"
            s = str()

        with open(file, "w") as ffile:
            ffile.write(str(args) + "\n")

        await save2db2(args, db)
        ejob.reset() if s else None
        await event.reply(
            f"<pre>\n<code class='language-Changed ffmpeg{s} CLI parameters to:'>{args}</code>\n</pre>",
            parse_mode="html",
        )
    except Exception:
        await logger(Exception)


async def check(event, args, client):
    """
    Get custom encoding params.
    Arguments:
        -2
        -3
        -4
        To check for ffmpeg2, 3 and 4 custom encoding params
    No argument to check first encoding params
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    if not args:
        file = ffmpeg_file
        args = str()
    elif "-2" in (args := args[:2]):
        file = ffmpeg_file2
    elif "-3" in args:
        file = ffmpeg_file3
    elif "-4" in args:
        file = ffmpeg_file4
    else:
        return

    if not file_exists(file):
        return await event.reply(
            "**Encoding params not found, use /set to set encoding params.**"
        )

    with open(file, "r") as ffile:
        ffmpeg = ffile.read().rstrip()

    await event.reply(
        f"<pre>\n<code class='language-Current ffmpeg{args[1:]} CLI parameters:'>{ffmpeg}</code>\n</pre>",
        parse_mode="html",
    )


async def reffmpeg(event, args, client):
    """
    Reset encoding params.
    Default value to reset to, it is either set in .env or contained in .config
    Arguments:
        -2
        -3
        -4
        To reset or unset ffmpeg2,3,4
        No argument for first encoding param
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    try:
        if args and (args := args[:2]) in ("-2", "-3", "-4"):
            return await reffmpeg2(event, args, client)
        with open(ffmpeg_file, "w") as file:
            file.write(str(conf.FFMPEG) + "\n")

        await save2db2(conf.FFMPEG, "ffmpeg")
        await event.reply(
            f"<pre>\n<code class='Reseted ffmpeg CLI parameters to:'>{conf.FFMPEG}</code>\n</pre>",
            parse_mode="html",
        )
    except Exception:
        await logger(Exception)


async def reffmpeg2(event, args, client):
    """
    Helper function to assist <reffmpeg>
    """
    try:
        s = args[1:]
        if "-2" in args:
            if not conf.FFMPEG2 and not file_exists(ffmpeg_file2):
                res = f"FFMPEG{s} not set in .env or bot."
            else:
                if file_exists(ffmpeg_file2):
                    s_remove(ffmpeg_file2)
                    await save2db2(None, f"ffmpeg{s}")
                    res = f"FFMPEG{s} params deleted.\nTry again to reset to the param in .env"
                else:
                    with open(ffmpeg_file2, "w") as file:
                        file.write(str(conf.FFMPEG2) + "\n")
                    await save2db2(conf.FFMPEG2, f"ffmpeg{s}")
                    res = f"<pre>\n<code class='Reseted ffmpeg{s} CLI parameters to:'>{conf.FFMPEG2}</code>\n</pre>"
        elif "-3" in args:
            if not conf.FFMPEG3 and not file_exists(ffmpeg_file3):
                res = f"FFMPEG{s} not set in .env or bot."
            else:
                if file_exists(ffmpeg_file3):
                    s_remove(ffmpeg_file3)
                    await save2db2(None, f"ffmpeg{s}")
                    res = f"FFMPEG{s} params deleted.\nTry again to reset to the param in .env"
                else:
                    with open(ffmpeg_file3, "w") as file:
                        file.write(str(conf.FFMPEG3) + "\n")
                    await save2db2(conf.FFMPEG3, f"ffmpeg{s}")
                    res = f"<pre>\n<code class='Reseted ffmpeg{s} CLI parameters to:'>{conf.FFMPEG3}</code>\n</pre>"
        elif "-4" in args:
            if not conf.FFMPEG4 and not file_exists(ffmpeg_file4):
                res = f"FFMPEG{s} not set in .env or bot."
            else:
                if file_exists(ffmpeg_file4):
                    s_remove(ffmpeg_file4)
                    await save2db2(None, f"ffmpeg{s}")
                    res = f"FFMPEG{s} params deleted.\nTry again to reset to the param in .env"
                else:
                    with open(ffmpeg_file4, "w") as file:
                        file.write(str(conf.FFMPEG4) + "\n")
                    await save2db2(conf.FFMPEG4, f"ffmpeg{s}")
                    res = f"<pre>\n<code class='Reseted ffmpeg{s} CLI parameters to:'>{conf.FFMPEG4}</code>\n</pre>"

        ejob.reset()
        await event.reply(
            res,
            parse_mode="html",
        )
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
        return await try_delete(event)
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
        return await try_delete(event)

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
        - {replace_caption} [Optional]
            • if not specified caption inherits replace_name.
            • if '0', a digit, is passed, filter is ignored for caption.
            • if '1', a digit, is passed, it is the same as not specifying.
            • if anything else is specified it uses that as caption name instead.
        - {replace_banner} [Optional]
            • if not specified, do nothing.
            • if '0', a digit, is passed, disables anilist for banner & thumbnail and banner inherits the result of {replace_caption}
            • if '1', a digit, is passed, value resulting from {replace_caption} is parsed by anilist for banner and thumbnail
            • if any other value is passed it is parsed by anilist for banner and thumbnail
        {replace_name}, {replace_caption} and {replace_banner} also accept '00', a double digit
        which essentially disables all fiter and anilist parsing for the anime_name.
        {replace_banner} cannot be set without {replace_caption} since it depends on it

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
        return await try_delete(event)
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
        return await try_delete(event)
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
        return await try_delete(event)
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
        -f  *(raw filter} [High priority]
        -rm {what to remove} removes the specified string from all filenames
            can be used with multiple items each separated/delimited with '|'
        -tf {filetag}
            • … <str> (force tag all file as your input without the '[]')
            • disable <str> (to disable)
            • auto <str> (tag files as usual) (default behaviour if argument is not specified)
        -tc {captag}
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
    *raw format:- 'what_to_remove\\ntag_file_as\\ntag_caption_as'
    *must specify an argument.

    Related commands:
        - /vfilter, /delfilter
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    try:
        arg = get_args("-f", "-rm", "-tc", "-tf", to_parse=args)
        if not arg.f and not arg.rm and not arg.tc and not arg.tf:
            return await event.reply(f"`{filter.__doc__}`")

        f = arg.rm or "__disabled."
        t = arg.tf or "auto"
        c = arg.tc or "auto"
        temp = string_escape(arg.f) or f"{f}\n{t}\n{c}"
        with open(filter_file, "w") as file:
            file.write(temp)
        await save2db2(temp, "filter")
        await event.reply("**Changed filters Successfully!**.")
        await asyncio.sleep(2)
        await vfilter(event, args, client)
    except Exception:
        await event.reply("Error Occurred")
        await logger(Exception)


async def vfilter(event, args, client):
    """View currently added filter."""
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
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
        return await try_delete(event)
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
        return await msg_sleep_delete(event, rply, time=20)
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
        return await try_delete(event)
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
            return await event.reply("No clue as to what " f"'`{args}`' means.")
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


async def fc_forward(msg, args, client):
    """Forwards replied message to conf.FCHANNEL"""
    if msg.from_user:
        if not user_is_owner(msg.from_user.id):
            return
    else:
        if msg.chat.id != conf.FCHANNEL:
            return
    try:
        if not conf.FCHANNEL:
            return await msg.reply("`conf.FCHANNEL var not set.`")
        if not msg.reply_to_message:
            return await msg.reply("`Reply with a message to forward to conf.FCHANNEL`")
        f_msg = msg.reply_to_message
        await f_msg.copy(chat_id=conf.FCHANNEL)
        rep = await msg.reply("`Forwarded succesfully.`")
        if args:
            await try_delete(msg)
            await try_delete(rep)
    except Exception:
        await logger(Exception)


async def rss_handler(event, args, client):
    """
    Base command for rss:
        *Arguments:
            -d (TITLE): To delete already an subscribed feed.
            -e (TITLE): To edit configurations for already subscribed rss feed.
            -g (TITLE, AMOUNT): To get previous feeds for given TITLE. (Amount corresponds to AMOUNT)
            -l (NO REQUIRED ARGS) To list subscribed feeds.
            -s (TITLE, LINK): To subscribe an rss feed.

        for additional help send the above arguments with -h/--help or without additional params.
        *listed in the order priority.
    """
    if not user_is_owner(event.sender_id):
        return await try_delete(event)
    arg, args = get_args(
        ["-d", "store_true"],
        ["-e", "store_true"],
        ["-g", "store_true"],
        ["-l", "store_true"],
        ["-s", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not (arg.d or arg.e or arg.g or arg.l or arg.s):
        return await avoid_flood(event.reply, f"`{rss_handler.__doc__}`")
    if arg.d:
        await event_handler(
            event, del_rss, client, True, default_args=args, use_default_args=True
        )
    elif arg.e:
        await event_handler(event, rss_editor, client, True, default_args=args)
    elif arg.g:
        await event_handler(event, rss_get, client, True, default_args=args)
    elif arg.l:
        await event_handler(event, rss_list, client, default_args=args)
    elif arg.s:
        await event_handler(event, rss_sub, client, True, default_args=args)


async def rss_list(event, args, client):
    """
    Get list of subscribed rss feeds
        Args:
            None.
        Returns:
            List of subscribed rss feeds.
    """
    if not user_is_owner(event.sender_id):
        return
    if not _bot.rss_dict:
        return await event.reply("<b> No subscriptions!</b>", parse_mode="html")
    list_feed = str()
    pre_event = event

    def parse_filter(ftr: str):
        if not ftr:
            return None
        return ", ".join(["(" + ", ".join(map(str, sublist)) + ")" for sublist in ftr])

    async with rss_dict_lock:
        for i, (title, data) in zip(itertools.count(1), list(_bot.rss_dict.items())):
            list_feed += f"\n\n{i}.<b>Title:</b> <code>{title}</code>\n<b>Feed Url: </b><code>{data['link']}</code>\n"
            list_feed += f"<b>Chat:</b> <code>{data['chat'] or 'Default'}</code>\n"
            list_feed += f"<b>Command:</b> <code>{data['command']}</code>\n"
            list_feed += f"<b>Direct:</b> <code>{data.get('direct', True)}</code>\n"
            list_feed += (
                f"<b>Include filter:</b> <code>{parse_filter(data['inf'])}</code>\n"
            )
            list_feed += (
                f"<b>Exclude filter:</b> <code>{parse_filter(data['exf'])}</code>\n"
            )
            list_feed += f"<b>Paused:</b> <code>{data['paused']}</code>"

    lmsg = await split_text(list_feed.strip("\n"), "\n\n", True)
    for i, msg in zip(itertools.count(1), lmsg):
        msg = f"<b>Your subscriptions</b> #{i}" + msg
        pre_event = await avoid_flood(pre_event.reply, msg, parse_mode="html")
        await asyncio.sleep(1)


async def rss_get(event, args, client):
    """
    Get the links of titles in rss:
    Arguments:
        [Title] - Title used in subscribing rss
        -a [Amount] - Amount of links to grab
    """
    if not user_is_owner(event.sender_id):
        return
    arg, args = get_args(
        "-a",
        ["-g", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not arg.a:
        if len(args.split()) != 2:
            return await event.reply(f"`{rss_get.__doc__}`")
        args, arg.a = args.split()
    if not arg.a.isdigit():
        return await event.reply("Second argument must be a digit.")

    title = args
    count = int(arg.a)
    data = _bot.rss_dict.get(title)
    if not (data and count > 0):
        return await event.reply(f"`{rss_get.__doc__}`")
    try:
        imsg = await event.reply(
            f"Getting the last <b>{count}</b> item(s) from {title}...",
            parse_mode="html",
        )
        pre_event = imsg
        html = await get_html(data["link"])
        rss_d = feedparse(html)
        item_info = ""
        for item_num in range(count):
            try:
                link = rss_d.entries[item_num]["links"][1]["href"]
            except IndexError:
                link = rss_d.entries[item_num]["link"]
            item_info += f"<b>Name: </b><code>{rss_d.entries[item_num]['title'].replace('>', '').replace('<', '')}</code>\n"
            item_info += f"<b>Link: </b><code>{link}</code>\n\n"
        for msg in await split_text(item_info, "\n\n"):
            pre_event = await avoid_flood(pre_event.reply, msg, parse_mode="html")
            await asyncio.sleep(2)
        await avoid_flood(
            imsg.edit,
            f"Here are the last <b>{count}</b> item(s) from {title}:",
            parse_mode="html",
        )
    except IndexError:
        await avoid_flood(
            imsg.edit, "Parse depth exceeded. Try again with a lower value."
        )
    except Exception as e:
        await logger(Exception)
        await avoid_flood(event.reply, f"error! - `{str(e)}`")


async def rss_editor(event, args, client):
    """
    Edit subscribed rss feeds!
    simply pass the rss title with the following arguements:
        Additional args:
            -c (/command): command to prefix the rss link
            --exf (what_to_exclude): keyword of words to fiter out*
            --inf (what_to_include): keywords to include*
            --chat (chat_id) chat to send rss overides RSS_CHAT pass 'default' to reset.
            -p () to pause the rss feed
            -r () to resume the rss feed
            --nodirect () disables rss direct
            --direct () enables rss direct

        *format = "x or y|z"
        *to unset pass 'disable' or 'off'
        where:
            or - means either of both values
            | - means and
        Returns:
            success message on successfully editing the rss configuration
    """
    if not user_is_owner(event.sender_id):
        return
    arg, args = get_args(
        "-c",
        "--exf",
        "--inf",
        "--chat",
        ["-e", "store_true"],
        ["-p", "store_true"],
        ["-r", "store_true"],
        ["--direct", "store_true"],
        ["--nodirect", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not args:
        return await event.reply(f"Please pass the title of the rss item to edit")
    if not (data := _bot.rss_dict.get(args)):
        return await event.reply(f"Could not find rss with title - {args}.")
    if not (
        arg.c
        or arg.exf
        or arg.inf
        or arg.p
        or arg.r
        or arg.chat
        or arg.direct
        or arg.nodirect
    ):
        return await event.reply("Please supply at least one additional arguement.")
    if arg.chat and not (
        arg.chat.lstrip("-").isdigit() or arg.chat.casefold() == "default"
    ):
        return await avoid_flood(
            event.reply,
            f"Chat must be a Telegram chat id (with -100 if a group or channel)\nNot '{arg.chat}'",
        )
    if arg.c:
        if not arg.c.startswith("/"):
            return await event.reply("'-c': arguement must start with '/'")
        data["command"] = arg.c
    if arg.chat:
        data["chat"] = int(arg.chat) if arg.chat.casefold() != "default" else None
    if arg.direct and arg.nodirect:
        await avoid_flood(event.reply, "**Warning:** Ignoring '--direct'")
    if arg.direct or arg.nodirect:
        data["direct"] = False if arg.nodirect else arg.direct
    if arg.exf:
        exf_lists = []
        if arg.exf.casefold() not in ("disable", "off"):
            filters_list = arg.exf.split("|")
            for x in filters_list:
                y = x.split(" or ")
                exf_lists.append(y)
        data["exf"] = exf_lists
    if arg.inf:
        inf_lists = []
        if arg.inf.casefold() not in ("disable", "off"):
            filters_list = arg.inf.split("|")
            for x in filters_list:
                y = x.split(" or ")
                inf_lists.append(y)
        data["inf"] = inf_lists
    if arg.p:
        data["paused"] = True
    elif arg.r:
        data["allow_rss_spam"] = True
        data["paused"] = False
        if scheduler.state == 2:
            scheduler.resume()
        elif not scheduler.running:
            schedule_rss()
            scheduler.start()
    await save2db2(_bot.rss_dict, "rss")
    await event.reply(
        f"Edited rss configurations for rss feed with title - `{args}` successfully!"
    )


async def del_rss(event, args, client):
    """
    Removes feed with designated title from list of subscribed feeds
        Args:
            TITLE (str): subscribed rss feed title to remove


        Returns:
            Success message on successfull removal
            Not found message if TITLE passed was not found
    """
    if not user_is_owner(event.sender_id):
        return
    if not _bot.rss_dict.get(args):
        return await event.reply(f"'{args}' not found in list of subscribed rss feeds!")
    _bot.rss_dict.pop(args)
    msg = f"Succesfully removed '{args}' from subscribed feeds!"
    await save2db2(_bot.rss_dict, "rss")
    await event.reply(msg)
    await logger(e=msg)


async def rss_sub(event, args, client):
    """
    Subscribe rss feeds!
    simply pass the rss link with the following arguements:
        Args:
            -t (TITLE): New Title of the subscribed rss feed [Required]
            -c (/command): command to prefix the rss link [Required]
            --exf (what_to_exclude): keyword of words to fiter out*
            --inf (what_to_include): keywords to include*
            -p () to pause the rss feed
            -r () to resume the rss feed
            --chat (chat_id) chat to send feeds
            --nodirect () to disable rss message getting passed directly* to bot
            --direct () to enable the above
                if not specified, defaults to RSS_DIRECT env.

        *format = "x or y|z"
        where:
            or - means either of both values
            | - means and
        *only leech and qbleech commands are passed
        Returns:
            success message on successfully editing the rss configuration
    """
    if not user_is_owner(event.sender_id):
        return
    arg, args = get_args(
        "-c",
        "-t",
        "--exf",
        "--inf",
        "--chat",
        ["--direct", "store_true"],
        ["--nodirect", "store_true"],
        ["-p", "store_true"],
        ["-s", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not (arg.c and arg.t and args):
        return await event.reply(f"`{rss_sub.__doc__}`")
    feed_link = args
    title = arg.t
    if not arg.c.startswith("/"):
        return await event.reply("'-c': arguement must start with '/'")
    if arg.chat and not arg.chat.lstrip("-").isdigit():
        return await avoid_flood(
            event.reply,
            f"Chat must be a Telegram chat id (with -100 if a group or channel)\nNot '{arg.chat}'",
        )
    if arg.direct and arg.nodirect:
        await avoid_flood(event.reply, "**Warning:** Ignoring '--direct'")
    if _bot.rss_dict.get(title):
        return await avoid_flood(
            event.reply,
            f"This title **{title}** has already been subscribed!. **Please choose another title!**",
        )
    inf_lists = []
    exf_lists = []
    msg = str()
    if arg.chat:
        arg.chat = int(arg.chat)
    if arg.inf:
        filters_list = arg.inf.split("|")
        for x in filters_list:
            y = x.split(" or ")
            inf_lists.append(y)
    if arg.exf:
        filters_list = arg.exf.split("|")
        for x in filters_list:
            y = x.split(" or ")
            exf_lists.append(y)
    if arg.nodirect:
        arg.direct = False
    elif not arg.direct:
        arg.direct = conf.RSS_DIRECT
    try:
        html = await get_html(feed_link)
        rss_d = feedparse(html)
        last_title = rss_d.entries[0]["title"]
        msg += "<b>Subscribed!</b>"
        msg += f"\n<b>Title: </b><code>{title}</code>\n<b>Feed Url: </b>{feed_link}"
        msg += f"\n<b>latest record for </b>{rss_d.feed.title}:"
        msg += f"\nName: <code>{last_title.replace('>', '').replace('<', '')}</code>"
        try:
            last_link = rss_d.entries[0]["links"][1]["href"]
        except IndexError:
            last_link = rss_d.entries[0]["link"]
        msg += f"\nLink:- <code>{last_link}</code>"
        msg += f"\n<b>Chat:- </b><code>{arg.chat or 'Default'}</code>"
        msg += f"\n<b>Command:- </b><code>{arg.c}</code>"
        msg += f"\n<b>Direct:- </b><code>{arg.direct}</code>"
        msg += f"\n<b>Filters:-</b>\ninf: <code>{arg.inf}</code>\nexf: <code>{arg.exf}<code/>"
        msg += f"\n<b>Paused:- </b><code>{arg.p}</code>"
        async with rss_dict_lock:
            _bot.rss_dict[title] = {
                "link": feed_link,
                "last_feed": last_link,
                "last_title": last_title,
                "chat": arg.chat,
                "command": arg.c,
                "direct": arg.direct,
                "inf": inf_lists,
                "exf": exf_lists,
                "paused": arg.p,
            }
        await logger(
            e="Rss Feed Added:"
            f"\nby:- {event.sender_id}"
            f"\ntitle:- {title}"
            f"\nlink:- {feed_link}"
            f"\nchat:- {arg.chat}"
            f"\ncommand:- {arg.c}"
            f"\ndirect:- {arg.direct}"
            f"\ninclude filter:- {arg.inf}"
            f"\nexclude filter:- {arg.exf}"
            f"\npaused:- {arg.p}"
        )
    except (IndexError, AttributeError) as e:
        emsg = f"The link: {feed_link} doesn't seem to be a RSS feed or it's region-blocked!"
        await avoid_flood(event.reply, emsg + "\nError: " + str(e))
    except Exception as e:
        await logger(Exception)
        return await avoid_flood(event.reply, str(e))
    await save2db2(_bot.rss_dict, "rss")
    if msg:
        await avoid_flood(event.reply, msg, parse_mode="html")
    if arg.p:
        return
    if scheduler.state == 2:
        scheduler.resume()
    elif not scheduler.running:
        schedule_rss()
        scheduler.start()
