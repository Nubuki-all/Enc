import asyncio
import html
import io
import sys
import traceback

from bot.config import _bot
from bot.utils.msg_utils import user_is_dev, user_is_owner
from bot.utils.os_utils import s_remove


async def eval(event, cmd, client):
    """
    Evaluate and execute code within bot.
    Global namespace has been cleaned so you'll need to manually import modules

    USAGE:
    Command requires code to execute as arguments.
    For example /eval print("Hello World!")
    Kindly refrain from adding whitelines and newlines between command and argument.
    """
    if not user_is_owner(event.sender_id):
        if not user_is_dev(event.sender_id):
            return
    msg = await event.reply("Processing ...")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, event)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    if len(evaluation) > 4000:
        final_output = "EVAL: {} \n\n OUTPUT: \n{} \n".format(cmd, evaluation)
        with io.BytesIO(str.encode(final_output)) as out_file:
            out_file.name = "eval.text"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=cmd,
            )
            await event.delete()
    else:
        final_output = "<pre>\n<code class='language-python'>{}</code>\n</pre>\n\n<pre>\n<code class='language-Output:'>{}</code>\n</pre>\n".format(
            html.escape(cmd), html.escape(evaluation)
        )
        await msg.edit(final_output, parse_mode="html")


async def aexec(code, event):
    res = {}
    exec(
        f"async def __aexec(event): " + "".join(f"\n {l}" for l in code.split("\n")),
        globals(),
        res,
    )
    return await res["__aexec"](event)


async def bash(event, cmd, client):
    """
    Run bash/system commands in bot
    Much care must be taken especially on Local deployment

    USAGE:
    Command requires executables as argument
    For example "/bash ls"
    """
    if not user_is_owner(event.sender_id):
        if not user_is_dev(event.sender_id):
            return
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    e = stderr.decode()
    if not e:
        e = "No Error"
    o = stdout.decode()
    if not o:
        o = "Tip:\nIf you want to see the results of your code, I suggest printing them to stdout."
    OUTPUT = f"QUERY:\n__Command:__\n{cmd} \n__PID:__\n{process.pid}\n\nstderr: \n{e}\nOutput:\n{o}"
    if len(OUTPUT) > 4000:
        with io.BytesIO(str.encode(OUTPUT)) as out_file:
            out_file.name = "exec.text"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=cmd,
            )
            return await event.delete()
    else:
        OUTPUT = f"<pre>\n<code class='language-bash'>{html.escape(cmd)}</code>\n</pre>\n<i>PID:</i>\n{process.pid}\n\n<pre>\n<code class='language-Stderr:'>{e}</code>\n</pre>\n<pre>\n<code class='language-Output:'>{html.escape(o)}</code>\n</pre>"
        await event.reply(OUTPUT, parse_mode="html")


async def aexec2(code, client, message):
    res = {}
    exec(
        f"async def __aexec2(client, message): "
        + "".join(f"\n {l}" for l in code.split("\n")),
        globals(),
        res,
    )
    return await res["__aexec2"](client, message)


async def eval_message_p(message, cmd, client):
    """
    Evaluate and execute code within bot.
    with pyrogram's bound message method instead.
    Global namespace has been cleaned so you'll need to manually import modules

    USAGE:
    Command requires code to execute as arguments.
    For example /peval print("Hello World!")
    Kindly refrain from adding whitelines and newlines between command and argument.
    """
    if not user_is_owner(message.from_user.id):
        return
    status_message = await message.reply_text("Processing ...")

    reply_to_id = message.id
    if message.reply_to_message:
        reply_to_id = message.reply_to_message.id

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None

    try:
        await aexec2(cmd, client, message)
    except Exception:
        exc = traceback.format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"

    final_output = "```python\n{}```\n\n```Output:\n{}```\n".format(
        cmd, evaluation.strip()
    )

    if len(final_output) > _bot.max_message_length:
        final_output = "Evaluated:\n{}\n\nOutput:\n{}".format(cmd, evaluation.strip())
        with open("eval.text", "w+", encoding="utf8") as out_file:
            out_file.write(str(final_output))
        await message.reply_document(
            document="eval.text",
            caption=cmd,
            disable_notification=True,
            reply_to_message_id=reply_to_id,
        )
        s_remove("eval.text")
        await status_message.delete()
    else:
        await status_message.edit(final_output)
