import time

from quote import quote
from random_word import RandomWords

from .emojis import enmoji


def enquotes():
    em = enmoji()
    res = str()
    start = time.time()
    while not res:
        try:
            if (time.time() - start) >= 20:
                return f"{em} **Nubuki-all:** `The feature 'quote' is currently broken, and has therefore been temporarily disabled.`"
            r = RandomWords()
            w = r.get_random_word()
            res = quote(w, limit=1)
            for i in range(len(res)):
                result = res[i]["quote"]
                result2 = res[i]["author"]
                output = (result[:2045] + "…") if len(result) > 2046 else result
                output = f"{em} **{result2}:** `{output}`"
        except Exception:
            time.sleep(0.5)
    return output
