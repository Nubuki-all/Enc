from quote import quote
from random_word import RandomWords

from .emojis import enmoji


async def enquotes():
    res = ""
    while not res:
        try:
            r = RandomWords()
            w = r.get_random_word()
            res = quote(w, limit=1)
            for i in range(len(res)):
                result = res[i]["quote"]
                result2 = res[i]["author"]
                y = enmoji()
                output = (result[:2045] + "…") if len(result) > 2046 else result
                output = f"{y} **{result2}:** `{output}`"
        except Exception:
            pass
    return output
