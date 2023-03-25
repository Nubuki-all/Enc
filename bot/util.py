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
            ne = f"\n\n**More Info:\n━━━━━━━━━━━━━━━━━━━**"
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


async def auto_rename(parsed_name, original_name, refunc):
    out_name = ""
    if refunc:
        for ren in refunc.split("\n"):
            ren = ren.strip()
            de_name = ren.split("|")[0].strip()
            re_name = ren.split("|")[1].strip()
            if original_name.casefold() == de_name.casefold():
                out_name = re_name
    if not out_name:
        out_name = parsed_name
    return out_name


async def get_codec():
    with open("ffmpeg.txt", "r") as file:
        ff_code = file.read().rstrip()
        file.close()
    s_check = dict()
    __out = ""
    s_check.update(
        {
            "480": "480p",
            "720": "720p",
            "1080": "1080p",
            "libx265": "HEVC",
            "libsvtav1": "AV1",
        }
    )
    for key, value in s_check.items():
        if key in ff_code:
            __out += f"[{value}] "
    return __out


async def wfilter():
    wname = Path("Namefilter.txt")
    wrelease = Path("Releasefilter.txt")
    aure = Path("Auto-rename.txt")

    if wname.is_file():
        with open("Namefilter.txt", "r") as file:
            wnamer = file.read().strip()
            file.close()
    else:
        wnamer = ""
    if wrelease.is_file():
        with open("Releasefilter.txt", "r") as file:
            wreleaser = file.read().strip()
            file.close()
    else:
        wreleaser = ""
    if aure.is_file():
        with open("Auto-rename.txt", "r") as file:
            aurer = file.read().strip()
            file.close()
    else:
        aurer = ""
    return wnamer, wreleaser, aurer


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
        wnamer, wreleaser, aurer = await wfilter()
        codec = await get_codec()
        con = ""
        olif = Path("filter.txt")
        temp_b = b
        if olif.is_file():
            fil2 = "" if fil2.casefold() == "disable" else fil2
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
                if fil2:
                    if fil2.casefold() == "auto":
                        fil2 = f"{json['countryOfOrigin']}"
                        fil2 = await conconvert(fil2)
            except Exception:
                ers = traceback.format_exc()
                LOGS.info(ers)
                fil2 = "" if fil2.casefold() == "auto" else fil2
            b = string.capwords(b)
            if len(b) > 33:
                cb = b[:32] + "…"
                cb = cb.split(":")[0]
            else:
                cb = b
            cb = await auto_rename(cb, temp_b, aurer)

            bb = ""
            bb += release_name
            bb += f" {cb}"
            if c:
                bb += f" S{c}"
            if d:
                bb += f" - {d}"
            if VERSION2:
                bb += f"v{VERSION2[0]}"
            if fil2:
                bb += f" [{fil2}]"
            bb2 = bb.replace(cb, b)
            bb2 = bb2.replace(release_name, release_name_b)
            if codec:
                bb2 += f" {codec}"
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
                col = ""
                if wreleaser:
                    for item in wreleaser.split("\n"):
                        if item.split("|")[0].casefold() in e.casefold():
                            if item.split("|")[1].casefold() != "disable":
                                wcol = item.split("|")[1]
                            else:
                                wcol = ""
                            break
                        else:
                            wcol = ""
                else:
                    wcol = ""
                if wnamer:
                    col = ""
                    for item in wnamer.split("\n"):
                        if item.startswith("^"):
                            if not item.split("|")[0] in name:
                                continue
                        else:
                            if not item.split("|")[0].casefold() in name.casefold():
                                continue
                        if item.split("|")[1].casefold() != "disable":
                            col = item.split("|")[1]
                        else:
                            col = ""
                        break
                    if not col and not wcol:
                        col = ""
                    elif wcol:
                        col = wcol
                else:
                    col = ""
                    col = wcol if wcol else col

                if col:
                    pass
                else:
                    col = con
            except Exception:
                ers = traceback.format_exc()
                LOGS.info(ers)
                g = ""
                col = ""

            if len(b) > 33:
                cb = b[:32] + "…"
                cb = cb.split(":")[0]
            else:
                cb = b
            cb = await auto_rename(cb, temp_b, aurer)

            bb = ""
            bb += release_name
            bb += f" {cb}"
            if c:
                bb += f" S{c}"
            if d:
                bb += f" - {d}"
            if VERSION2:
                bb += f"v{VERSION2[0]}"
            if g == d:
                bb += " [END]"
            if col:
                bb += f" [{col}]"
            bb2 = bb.replace(cb, b)
            bb2 = bb2.replace(release_name, release_name_b)
            if codec:
                bb2 += f" {codec}"
            bb += ".mkv"
    except Exception:
        ers = traceback.format_exc()
        LOGS.info(ers)
        bb = kk.replace(f".{aa}", f" {C_LINK}")
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
    return b, d, c, e


async def custcap(name, fname):
    try:
        oi, z, y, e, fil2, fil3, s, st = await parser(name)
        if oi is None:
            raise Exception("Parsing Failed")
        cdp = CAP_DECO
        temp_oi = oi
        wnamer, wreleaser, aurer = await wfilter()
        codec = await get_codec()
        try:
            fil3t = ""
            if wreleaser:
                for item in wreleaser.split("\n"):
                    if item.split("|")[0].casefold() in e.casefold():
                        if item.split("|")[2].casefold() != "disable":
                            wfil3t = item.split("|")[2]
                            break
                        else:
                            wfil3t = ""
                    else:
                        wfil3t = ""
            else:
                wfil3t = ""
            if wnamer:
                fil3t = ""
                for item in wnamer.split("\n"):
                    if item.startswith("^"):
                        if not item.split("|")[0] in name:
                            continue
                    else:
                        if not item.split("|")[0].casefold() in name.casefold():
                            continue
                    if item.split("|")[2].casefold() != "disable":
                        fil3t = item.split("|")[2]
                    else:
                        fil3t = ""
                    break
                if not fil3t and not wfil3t:
                    fil3t = ""
                elif wfil3t:
                    fil3t = wfil3t
            else:
                fil3t = ""
                fil3t = wfil3t if wfil3t else fil3t

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
        oi = await auto_rename(oi, temp_oi, aurer)
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
            caption += f"\n**{cdp} (V{VERSION2[0]}) Reason:** `{VERSION2[1]}`"
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
        if codec:
            caption += f"**🌟:** `{codec}`\n"
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
        caption = f"**{ot}**\n**🔗 {C_LINK}**"
    return caption
