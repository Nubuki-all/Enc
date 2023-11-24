import asyncio

from quote import quote
from random_word import RandomWords

from .emojis import enmoji


async def enquotes():
    res = str()
    em = enmoji()
    return f"{em} **Nubuki-all:** `The feature 'quote' is currently broken, and has therefore been disabled.`"
    while not res:
        try:
            r = RandomWords()
            w = r.get_random_word()
            res = quote(w, limit=1)
            for i in range(len(res)):
                result = res[i]["quote"]
                result2 = res[i]["author"]
                output = (result[:2045] + "…") if len(result) > 2046 else result
                output = f"{em} **{result2}:** `{output}`"
        except Exception:
            await asyncio.sleep(0.5)
    return output
