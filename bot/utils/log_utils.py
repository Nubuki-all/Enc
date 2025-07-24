import inspect
import logging
import traceback

from bot import conf, tele
from bot.fun.emojis import enmoji

_log_ = logging.getLogger(__name__)


def get_logger_from_caller():
    """
    Walk up the call stack until you find a frame whose module name
    isn’t this one, and return a Logger for that module.
    """
    current_module = __name__
    frame = inspect.currentframe()
    # skip our own get_logger_from_caller frame
    frame = frame.f_back
    max_look_backs = 4

    while frame and max_look_backs:
        module = inspect.getmodule(frame)
        name = module.__name__ if module else None
        # first frame not in this module → the caller
        if name and name != current_module:
            return logging.getLogger(name)
        frame = frame.f_back
        max_look_backs -= 1

    # fallback if all else fails
    return logging.getLogger(current_module)


async def group_logger(
    Exception: Exception = None,
    e: str = None,
    critical: bool = False,
    debug: bool = False,
    error: bool = False,
    warning: bool = False,
):
    if not (conf.LOG_CHANNEL and conf.LOGS_IN_CHANNEL):
        return
    try:
        if critical:
            pre = "CRITICAL ERROR"
        elif debug:
            pre = "DEBUG"
        elif warning:
            pre = "WARNING"
        elif error or not e:
            pre = "ERROR"
        else:
            pre = "INFO"
        trace = e or traceback.format_exc()
        msg = await tele.send_message(
            conf.LOG_CHANNEL,
            f"**#{pre}\n\n⛱️ Summary of what happened:**\n`{trace}`\n\n**To restict error messages to logs set the** `conf.LOGS_IN_CHANNEL` **env var to** `False`. {enmoji()}",
        )
        return msg
    except Exception:
        _log_.error(traceback.format_exc())


def log(
    Exception: Exception = None,
    e: str = None,
    critical: bool = False,
    debug: bool = False,
    error: bool = False,
    warning: bool = False,
    logger=None,
):
    trace = e or traceback.format_exc()
    logger = logger or get_logger_from_caller()

    if critical:
        logger.critical(trace)
    elif debug:
        logger.debug(trace)
    elif warning:
        logger.warning(trace)
    elif error or not e:
        logger.error(trace)
    else:
        logger.info(trace)


async def logger(
    Exception: Exception = None,
    e: str = None,
    critical: bool = False,
    debug: bool = False,
    error: bool = False,
    warning: bool = False,
):
    logger = get_logger_from_caller()
    log(Exception, e, critical, debug, error, warning, logger)
    await group_logger(Exception, e, critical, debug, error, warning)
