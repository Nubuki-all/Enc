import string
import zlib

import anitopy
import country_converter as coco
import flag
import pycountry
import requests

from . import *
from .funcn import *

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
            ne = f"\n\n**Video/file information:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**"
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


async def auto_rename(parsed_name, original_name, refunc, caption=False):
    out_name = ""
    if refunc:
        for ren in refunc.split("\n"):
            ren = ren.strip()
            de_name = ren.split("|")[0].strip()
            re_name = ren.split("|")[1].strip()
            if original_name.casefold() == de_name.casefold():
                out_name = re_name
            else:
                continue
            if caption and len(ren.split("|")) > 2:
                cap_name = ren.split("|")[2].strip()
                if str(cap_name) == "0":
                    out_name = parsed_name
                elif str(cap_name) == "1":
                    out_name = re_name
                else:
                    out_name = cap_name
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
    return __out.strip()


async def get_stream_info(file):
    try:
        if not file.is_file():
            return None, None
        out = await enshell(
            f'ffprobe -hide_banner -show_streams -print_format json """{file}"""'
        )
        details = json.loads(out[1])
        a_lang = ""
        s_lang = ""
        for stream in details["streams"]:
            stream["index"]
            try:
                stream["codec_name"]
            except BaseException:
                continue
            stream_type = stream["codec_type"]
            if stream_type not in ("audio", "subtitle"):
                continue
            if stream_type == "audio":
                try:
                    a_lang += stream["tags"]["language"] + "|"
                except BaseException:
                    a_lang += "?|"
            elif stream_type == "subtitle":
                try:
                    s_lang += stream["tags"]["language"] + "|"
                except BaseException:
                    s_lang += "?|"
    except KeyError as k_e:
        if not str(k_e) == "'streams'":
            ers = traceback.format_exc()
            await channel_log(ers)
            LOGS.info(ers)
        else:
            LOGS.info("[NOTICE] No stream was found.")
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)
    return (a_lang.strip("|"), s_lang.strip("|"))


async def pos_in_stm(file, lang1="eng", lang2="eng-us"):
    try:
        if not (Path(file)).is_file():
            return None, None
        a_pos = ""
        s_pos = ""
        _ainfo, _sinfo = await get_stream_info(Path(file))
        i = 1
        for audio in _ainfo.split("|"):
            if audio == lang1 or audio == lang2:
                a_pos = i
                break
            i = i + 1
        i = 1
        for subs in _sinfo.split("|"):
            if subs == lang1 or audio == lang2:
                s_pos = i
            i = i + 1
    except Exception:
        ers = traceback.format_exc()
        await channel_log(ers)
        LOGS.info(ers)
    return a_pos, s_pos

async def wfilter():
    wname = Path("Namefilter.txt")
    wrelease = Path("Releasefilter.txt")
    aure = Path("Auto-rename.txt")
    wrecap = Path("Release_caption.txt")

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
    if wrecap.is_file():
        with open(wrecap, "r") as file:
            wrecaper = file.read().strip()
            file.close()
    else:
        wrecaper = ""
    return wnamer, wreleaser, aurer, wrecaper


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
            if str(c) == "01" or str(c) == "1":
                c = ""
        except Exception:
            c = ""
        try:
            e = na["release_group"]
        except Exception:
            e = ""
        try:
            r = f'[{na["release_information"]}]'
        except Exception:
            r = ""
        try:
            st = na["episode_title"]
            st = "" if st == "END" else st
            st = "" if "MULTi" in st else st
        except Exception:
            st = ""
        try:
            yr = na["anime_year"]
            if b:
                b = b + " " + yr
        except Exception:
            pass
        return na, b, d, c, e, fil2, fil3, st, r
    except Exception:
        pass


async def conconvert(iso2_codes):
    try:
        iso3_codes = coco.convert(names=iso2_codes, to="ISO3").capitalize()
    except Exception as er:
        LOGS.info(er)
    return iso3_codes


async def parse(name, kk="", aa=".mkv"):
    try:
        ani, b, d, c, e, fil2, fil3, st, r = await parser(name)
        if b is None:
            raise Exception("Parsing Failed")
        if not kk:
            kk = name
        _infile = Path("downloads/" + kk)
        if not _infile.is_file():
            _infile = Path("thumb/" + kk)
        wnamer, wreleaser, aurer, wrecaper = await wfilter()
        r_is_end = False
        r_is_end = True if r == "[END]" else r_is_end
        codec = await get_codec()
        con = ""
        olif = Path("filter.txt")
        temp_b = b
        try:
            ttx = Path("parse.txt")
            if ttx.is_file():
                raise Exception("Parsing Turned off")
            variables = {"search": b, "type": "ANIME"}
            json = (
                requests.post(url, json={"query": anime_query, "variables": variables})
                .json()["data"]
                .get("Media")
            )
            try:
                b = f"{json['title']['english']}"
                b = f"{json['title']['romaji']}" if b == "None" else b
                con = f"{json['countryOfOrigin']}"
                con = await conconvert(con)
                g = f"{json.get('episodes')}"
                g = "0" + str(g) if d.startswith("0") else g
            except Exception:
                con = ""
                g = ""

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
                        if not item.split("|")[0].lstrip("^") in name:
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

        except Exception:
            ers = traceback.format_exc()
            LOGS.info(ers)
            col = ""

        if col:
            pass
        else:
            col = con

        a_check, _none = await get_stream_info(_infile)
        if a_check:
            if len(a_check.split("|")) > 3:
                col = "MULTi"
            elif len(a_check.split("|")) == 3:
                col = "Tri"
            elif len(a_check.split("|")) == 2:
                col = "Dual"
        elif a_check is None:
            col = "TBD"

        if olif.is_file() and fil2.casefold() != "auto":
            col = fil2
            col = "" if fil2.casefold() == "disable" else col
        else:
            pass
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
        if g == d and not c or r_is_end:
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
        bb = kk.replace(f".{aa}", f" {C_LINK}.{aa}")
        bb2 = bb
    if "/" in bb:
        bb = bb.replace("/", " ")
    return bb, bb2


async def dynamicthumb(name, thum="thumb2.jpg"):
    try:
        ani, b, d, c, e, fil2, fil3, st, r = await parser(name)
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
            os.system(f"wget {mog} -O {thum}")
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
        ani, oi, z, y, e, fil2, fil3, st, r = await parser(name)
        if oi is None:
            raise Exception("Parsing Failed")
        out = Path("encode/" + fname)
        if not out.is_file():
            out = Path("thumb/" + fname)
        cdp = CAP_DECO
        temp_oi = oi
        wnamer, wreleaser, aurer, wrecaper = await wfilter()
        r_is_end = False
        r_is_end = True if r == "[END]" else r_is_end
        codec = await get_codec()
        try:
            wfil3t = ""
            fil3t = ""
            wrefil3t = ""
            if wreleaser:
                for item in wreleaser.split("\n"):
                    if item.split("|")[0].casefold() in e.casefold():
                        if item.split("|")[2].casefold() != "disable":
                            wfil3t = item.split("|")[2]
                            break
                        else:
                            break

            if wnamer:
                for item in wnamer.split("\n"):
                    if item.startswith("^"):
                        if not item.split("|")[0].lstrip("^") in name:
                            continue
                    else:
                        if not item.split("|")[0].casefold() in name.casefold():
                            continue
                    if item.split("|")[2].casefold() != "disable":
                        fil3t += item.split("|")[2] + " "
                    if item.startswith("^"):
                        break

            fil3t = wfil3t if wfil3t else fil3t

            _ainfo, _sinfo = await get_stream_info(out)
            if fil3t:
                fil3t = fil3t.strip()
            else:
                if _ainfo or _sinfo:
                    fil3t = ""
                    if _ainfo:
                        audio_count = len(_ainfo.split("|"))
                        if audio_count > 3:
                            fil3t += f"(Multi-Audio)[{audio_count}] "
                        elif audio_count == 3:
                            fil3t += "(Tri-Audio)"
                        elif audio_count == 2:
                            fil3t += f"(Dual-Audio)"
                    if _sinfo:
                        sub_count = len(_sinfo.split("|"))
                        if sub_count > 2:
                            fil3t += f"(Multi-Subs)[{sub_count}] "
                        else:
                            fil3t += "(Subs: "
                            for subs in _sinfo.split("|"):
                                fil3t += f"[{subs}] "
                            fil3t = fil3t.strip()
                            fil3t += ")"
                else:
                    fil3t = "(English subtitle)"

            if wrecaper:
                for item in wrecaper.split("\n"):
                    _check_r = item.split("||", maxsplit=1)
                    if _check_r[0] in e:
                        for items in _check_r[1].split("||"):
                            if items.split("|")[0] in name:
                                wrefil3t = items.split("|")[1]
                        break

            fil3t = wrefil3t + " : " + fil3t if wrefil3t else fil3t

        except Exception:
            pass
        try:
            adi = ani["source"]
        except Exception:
            adi = ""
        olif = Path("filter.txt")
        if olif.is_file() and fil3.casefold() != "auto":
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
            if y:
                variables = {"search": f"{oi} {y}", "type": "ANIME"}
                json = (
                    requests.post(
                        url, json={"query": anime_query, "variables": variables}
                    )
                    .json()["data"]
                    .get("Media")
                )
            g = f"{json.get('episodes')}"
            g = "0" + str(g) if z.startswith("0") else g
        except Exception:
            g = ""
        oi = string.capwords(oi)
        oi = await auto_rename(oi, temp_oi, aurer, caption=True)
        crc32s = await crc32(out)
        try:
            a2 = await info(out, e)
        except Exception:
            a2 = ""
        caption = f"**{cdp} Title:** `{oi}`\n"
        if z:
            caption += f"**{cdp} Episode:** `{z}`"
            if VERSION2:
                caption += f" (v{VERSION2[0]})"
        if VERSION2:
            if not z or WORKING:
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
        if not r_is_end:
            caption += f" `{r}`"
        if z == g or r_is_end:
            caption += " **[END]**\n"
        else:
            caption += "\n"
        if st:
            caption += f"**{cdp} Episode Title:** `{st}`\n"
        if codec:
            caption += f"**🌟:** `{codec}`"
            if adi:
                caption += f" `[{adi}]`"
            caption += "\n"
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


async def f_post(name, out):
    try:
        ani, b, d, c, e, fil2, fil3, st, r = await parser(name)
        _ainfo, _sinfo = await get_stream_info(Path(out))
        pb = b
        if FCODEC:
            codec = FCODEC
        else:
            codec = await get_codec()
        try:
            ttx = Path("parse.txt")
            if ttx.is_file():
                raise Exception("Parsing turned off")
            if c:
                pb = b + " " + c
            variables = {"search": b, "type": "ANIME"}
            json = (
                requests.post(url, json={"query": anime_query, "variables": variables})
                .json()["data"]
                .get("Media")
            )
            variables = {"search": pb, "type": "ANIME"}
            json2 = (
                requests.post(url, json={"query": anime_query, "variables": variables})
                .json()["data"]
                .get("Media")
            )
            b = json["title"]["english"]
            b = f"{json['title']['romaji']}" if b == "None" else b
            br = json["title"]["romaji"]
            try:
                id_ = json2["id"]
            except Exception:
                id_ = json["id"]
            pic_url = f"https://img.anili.st/media/{id_}"
            con = f"{json['countryOfOrigin']}"
            try:
                gen = json["genres"]
            except Exception:
                gen = None

        except Exception:
            br = "N/A"
            cflag = con = "?"
            gen = None
            pic_url = "https://upload.wikimedia.org/wikipedia/commons/d/d1/Image_not_available.png"
        a_lang = ""
        s_lang = ""

        def get_flag(lang_t):
            if not lang_t == "?":
                if "-" in lang_t:
                    lang_t1, lang_t2 = lang_t.split("-", maxsplit=1)
                    if lang_t2.isdigit():
                        lang_t = lang_t1
                    else:
                        lang_t = lang_t2
                if lang_t.casefold() == "eng":
                    lang_t = "US"
                elif lang_t.casefold() == "ara":
                    lang_t = "Arabia"
                elif lang_t.casefold() == "hin":
                    lang_t = "ind"
                elif lang_t.casefold() == "ind":
                    lang_t = "Indonesia"
                lang_t = pycountry.countries.search_fuzzy(lang_t)
                lang_t = lang_t[0].alpha_2
                lang_t = flag.flag(lang_t)
            return lang_t

        if _ainfo:
            for a_lang_t in _ainfo.split("|"):
                a_lang += get_flag(a_lang_t)
                a_lang += ", "
            a_lang = a_lang.strip(", ")
        else:
            a_lang = "N/A"
        if _sinfo:
            for s_lang_t in _sinfo.split("|"):
                s_lang += get_flag(s_lang_t)
                s_lang += ", "
            s_lang = s_lang.strip(", ")
        else:
            s_lang = "N/A"
        if not con == "?":
            cflag = flag.flag(con)
        if gen:
            genre = ""
            for x in gen:
                genre += "#" + (x.replace(" ", "_")).replace("-", "_") + " "

        msg = f"[{cflag}]"
        if b == br:
            msg += f"`{b}`"
        else:
            msg += f"**{br}** | `{b}`"
        msg += "\n\n"
        if gen and genre:
            msg += f"**‣ Genre** : {genre}\n"
        if d:
            msg += f"**‣ Episode** : `{d}`\n"
        if c:
            msg += f"**‣ Season** : `{c}`\n"
        msg += f"**‣ Quality** : `{codec}`\n"
        msg += f"**‣ Audio(s)** : `{a_lang}`\n"
        msg += f"**‣ Subtitle(s)** : `{s_lang}`\n"
    except Exception:
        pic_url = None
        msg = None
        ers = traceback.format_exc()
        LOGS.info(ers)
    return pic_url, msg
