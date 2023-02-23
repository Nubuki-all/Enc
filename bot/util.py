import string
import zlib

import anitopy
import country_converter as coco
import requests

from . import *
from .funcn import UNLOCK_UNSTABLE, VERSION2, WORKING, info

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f"{round(size_in_bytes, 2)}{SIZE_UNITS[index]}"
    except IndexError:
        return "File too large"


def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result


async def parse_dl(filename):
    if UNLOCK_UNSTABLE:
        try:
            na = anitopy.parse(filename)
        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)
            na = ""
            ne = f"\n\n**Filename:** `{filename}`"
        if na:
            for key, value in na.items():
                ne += f"\n**{key}:** `{value}`"

    else:
        ne = "…"
    return ne


async def crc32(filename, chunksize=65536):
    """Compute the CRC-32 checksum of the contents of the given filename"""
    with open(filename, "rb") as f:
        checksum = 0
        while chunk := f.read(chunksize):
            checksum = zlib.crc32(chunk, checksum)
        return "%X" % (checksum & 0xFFFFFFFF)


async def wfilter():
    wname = Path("Namefilter.txt")
    wrelease = Path("Releasefilter.txt")
    if wname.is_file():
        with open("Namefilter.txt", "r") as file:
            wnamer = file.read().strip
            file.close()
    else:
        wnamer = ""
    if wrelease.is_file():
        with open("Releasefilter.txt", "r") as file:
            wreleaser = file.read().strip()
            file.close()
    else:
        wreleaser = ""
    return wnamer, wreleaser


url = "https://graphql.anilist.co"
anime_query = """
query ($id: Int, $idMal:Int, $search: String, $type: MediaType, $asHtml: Boolean) {
  Media (id: $id, idMal: $idMal, search: $search, type: $type) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    format
    status
    description (asHtml: $asHtml)
    startDate {
      year
      month
      day
    }
    season
    episodes
    duration
    countryOfOrigin
    source (version: 2)
    trailer {
      id
      site
      thumbnail
    }
    coverImage {
      extraLarge
    }
    bannerImage
    genres
    averageScore
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    isAdult
    characters (role: MAIN, page: 1, perPage: 10) {
      nodes {
        id
        name {
          full
          native
        }
        image {
          large
        }
        description (asHtml: $asHtml)
        siteUrl
      }
    }
    studios (isMain: true) {
      nodes {
        name
        siteUrl
      }
    }
    siteUrl
  }
}
"""


async def parser(name):
    try:
        olif = Path("filter.txt")
        if olif.is_file():
            with open("filter.txt", "r") as file:
                fil = file.read()
                fil1 = fil.split("\n")[0]
                fil2 = fil.split("\n")[1]
                fil3 = fil.split("\n")[2]
                file.close()
        else:
            fil1 = ""
            fil2 = ""
            fil3 = ""
        if olif.is_file() and fil1.casefold() != "disable":
            for i in fil1.split("|"):
                name = name.replace(i, "")
        if fil3.casefold() == "disable":
            fil3 = ""
        na = anitopy.parse(f"{name}")
        print(na)
        try:
            b = na["anime_title"]
        except Exception:
            b = ""
        try:
            d = na["episode_number"]
        except Exception:
            d = ""
        try:
            c = na["anime_season"]
            c = c.lstrip("0") if int(c) > 1 else c
        except Exception:
            c = ""
        try:
            e = na["release_group"]
        except Exception:
            e = ""
        try:
            s = na["subtitles"]
        except Exception:
            s = ""
        try:
            st = na["episode_title"]
            st = "" if st == "END" else st
            st = "" if "MULTi" in st else st
        except Exception:
            st = ""
        return b, d, c, e, fil2, fil3, s, st
    except Exception:
        pass


async def conconvert(iso2_codes):
    try:
        iso3_codes = coco.convert(names=iso2_codes, to="ISO3").capitalize()
    except Exception as er:
        LOGS.info(er)
    return iso3_codes


async def parse(name, kk, aa):
    try:
        b, d, c, e, fil2, fil3, s, st = await parser(name)
        if b is None:
            raise Exception("Parsing Failed")
        cb2 = "[ANi-MiNE]"
        wnamer, wreleaser = await wfilter()
        with open("ffmpeg.txt", "r") as file:
            nani = file.read().rstrip()
            file.close()
        con = ""
        olif = Path("filter.txt")
        if olif.is_file():
            try:
                ttx = Path("parse.txt")
                if ttx.is_file():
                    raise Exception("Parsing turned off")
                variables = {"search": b, "type": "ANIME"}
                json = (
                    requests.post(
                        url, json={"query": anime_query, "variables": variables}
                    )
                    .json()["data"]
                    .get("Media")
                )
                b = f"{json['title']['english']}"
                b = f"{json['title']['romaji']}" if b == "None" else b
                if fil2.casefold() == "auto":
                    fil2 = f"{json['countryOfOrigin']}"
                    fil2 = await conconvert(fil2)
                fil2 = "" if fil2.casefold() == "disable" else fil2
            except Exception:
                ers = traceback.format_exc()
                LOGS.info(ers)
                fil2 = "" if fil2 == "Disable" else fil2
            b = string.capwords(b)
            if len(b) > 33:
                cb = b[:32] + "…"
                cb = cb.split(":")[0]
            else:
                cb = b
            bb = ""
            bb += "[A-M]"
            bb += f" {cb}"
            if c:
                bb += f" S{c}"
            if d:
                bb += f" - {d}"
            if VERSION2:
                bb += "v2"
            if fil2:
                bb += f" [{fil2}]"
            bb2 = bb.replace(cb, b)
            bb2 = bb2.replace("[A-M]", cb2)
            if "1080" in nani:
                bb2 += " | [1080p]"
            bb += ".mkv"
        else:
            try:
                ttx = Path("parse.txt")
                if ttx.is_file():
                    raise Exception("Parsing Turned off")
                variables = {"search": b, "type": "ANIME"}
                json = (
                    requests.post(
                        url, json={"query": anime_query, "variables": variables}
                    )
                    .json()["data"]
                    .get("Media")
                )
                b = f"{json['title']['english']}"
                b = f"{json['title']['romaji']}" if b == "None" else b
                con = f"{json['countryOfOrigin']}"
                con = await conconvert(con)
                g = f"{json.get('episodes')}"
                b = string.capwords(b)
                if len(b) > 33:
                    cb = b[:32] + "…"
                    cb = cb.split(":")[0]
                else:
                    cb = b
                col = ""
                if wreleaser:
                    for item in wreleaser.split("\n"):
                        if item.split(":")[0] in e:
                            if item.split(":")[1] != "Disable":
                                wcol = item.split(":")[1]
                                break
                            else:
                                wcol = ""
                        else:
                            wcol = ""
                if wnamer:
                    for item in wnamer.split("\n"):
                        if item.split(":")[0] in name:
                            if item.split(":")[1] != "Disable":
                                col = item.split(":")[1]
                                break
                            else:
                                col = ""
                        else:
                            if wcol:
                                col = wcol
                            else:
                                col = ""
                if col:
                    pass
                else:
                    col = con
            except Exception:
                ers = traceback.format_exc()
                LOGS.info(ers)
                g = ""
                col = ""
                cb = b
            bb = ""
            bb += "[A-M]"
            bb += f" {cb}"
            if c:
                bb += f" S{c}"
            if d:
                bb += f" - {d}"
            if VERSION2:
                bb += "v2"
            if g == d:
                bb += " [END]"
            if col:
                bb += f" [{col}]"
            bb2 = bb.replace(cb, b)
            bb2 = bb2.replace("[A-M]", cb2)
            if "1080" in nani:
                bb2 += " | [1080p]"
            bb += ".mkv"
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        bb = kk.replace(f".{aa}", " @Ani_Mine.mkv")
        bb2 = bb
    if "/" in bb:
        bb = bb.replace("/", " ")
    return bb, bb2


async def dynamicthumb(name, kk, aa):
    try:
        b, d, c, e, fil2, fil3, s, st = await parser(name)
        try:
            ttx = Path("parse.txt")
            if ttx.is_file():
                raise Exception("Parsing turned off")
            variables = {"search": b, "type": "ANIME"}
            json = (
                requests.post(url, json={"query": anime_query, "variables": variables})
                .json()["data"]
                .get("Media")
            )
            ba = f"{json['title']['english']}"
            ba = f"{json['title']['romaji']}" if ba == "None" else ba
        except Exception:
            pass
        if c:
            coy = c.replace("0", "")
            coy = f"{ba} {coy}"
        else:
            coy = ba
        try:
            ttx = Path("parse.txt")
            if ttx.is_file():
                raise Exception("Parsing turned off")
            variables = {"search": coy, "type": "ANIME"}
            json = (
                requests.post(url, json={"query": anime_query, "variables": variables})
                .json()["data"]
                .get("Media")
            )
            mog = f"{json.get('coverImage')['extraLarge']}"
            os.system(f"wget {mog} -O thumb2.jpg")
        except Exception:
            try:
                ttx = Path("parse.txt")
                if ttx.is_file():
                    raise Exception("Parsing turned off")
                variables = {"search": b, "type": "ANIME"}
                json = (
                    requests.post(
                        url, json={"query": anime_query, "variables": variables}
                    )
                    .json()["data"]
                    .get("Media")
                )
                mog = f"{json.get('coverImage')['extraLarge']}"
                os.system(f"wget {mog} -O thumb2.jpg")
            except Exception:
                pass
    except Exception:
        pass
    return b, d, e


async def custcap(name, fname):
    try:
        oi, z, y, e, fil2, fil3, s, st = await parser(name)
        if oi is None:
            raise Exception("Parsing Failed")
        cdp = CAP_DECO
        with open("ffmpeg.txt", "r") as file:
            nani = file.read().rstrip()
            file.close()
        wnamer, wreleaser = await wfilter()
        try:
            fil3t = ""
            if wreleaser:
                for item in wreleaser.split("\n"):
                    if item.split(":")[0] in e:
                        if item.split(":")[2] != "Disable":
                            wfil3t = item.split(":")[2]
                            break
                        else:
                            wfil3t = ""
                    else:
                        wfil3t = ""
            if wnamer:
                for item in wnamer.split("\n"):
                    if item.split(":")[0] in name:
                        if item.split(":")[2] != "Disable":
                            fil3t = item.split(":")[2]
                            break
                        else:
                            fil3t = ""
                    else:
                        if wfil3t:
                            fil3t = wfil3t
                        else:
                            fil3t = ""
            if fil3t:
                pass
            else:
                if s:
                    fil3t = s
                else:
                    fil3t = "English Subtitle"
        except Exception:
            pass
        olif = Path("filter.txt")
        if olif.is_file():
            pass
        else:
            fil3 = fil3t
        try:
            ttx = Path("parse.txt")
            if ttx.is_file():
                raise Exception("Parsing turned off")
            variables = {"search": oi, "type": "ANIME"}
            json = (
                requests.post(url, json={"query": anime_query, "variables": variables})
                .json()["data"]
                .get("Media")
            )
            oi = f"{json['title']['english']}"
            oi = f"{json['title']['romaji']}" if oi == "None" else oi
            g = f"{json.get('episodes')}"
        except Exception:
            g = ""
        oi = string.capwords(oi)
        out = f"encode/{fname}"
        crc32s = await crc32(out)
        try:
            a2 = await info(out, e)
        except Exception:
            a2 = ""
        caption = f"**{cdp} Title:** `{oi}`\n"
        if z:
            caption += f"**{cdp} Episode:** `{z}`"
        if VERSION2:
            caption += " (v2)"
        if VERSION2 and WORKING:
            caption += f"\n**{cdp} (V2) Reason:** `{VERSION2[0]}`"
        if z:
            caption += "\n"
        if y:
            caption += f"**{cdp} Season:** `{y}`\n"
        if fil3 and a2:
            fil3 = fil3.format(**locals())
            caption += f"**{cdp} Type:** [{fil3}]({a2})"
        else:
            fil3 = fil3.format(**locals())
            caption += f"**{cdp} Type:** `{fil3}`"
        if z == g:
            caption += " **[END]**\n"
        else:
            caption += "\n"
        if st:
            caption += f"**{cdp} Episode Title:** `{st}`\n"
        if "1080" in nani:
            caption += f"**🌟:** `[1080p] [AV1]`\n"
        if ENCODER:
            encr = ENCODER.replace("@", "")
            caption += f"**{cdp} Encoder:** `{encr}`\n"
        caption += f"**{cdp} CRC32:** `[{crc32s}]`\n"
        caption += "**🔗 @ANi_MiNE**"
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        om = fname.split(".")[0]
        ot = om.split("@")[0]
        caption = f"**{ot}**\n**🔗 @Ani_Mine**"
    return caption
