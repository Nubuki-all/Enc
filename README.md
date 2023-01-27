# Encode2Tg [BETA] [![pyLint](https://github.com/Niffy-the-conqueror/Encode2Tg/actions/workflows/pyLint.yml/badge.svg?branch=anime)](https://github.com/Niffy-the-conqueror/Encode2Tg/actions/workflows/pyLint.yml)
[![Build Status](https://dev.azure.com/itsjustplainr/E2tg/_apis/build/status/Niffy-the-conqueror.Encode2Tg?branchName=anime&jobName=Work)](https://dev.azure.com/itsjustplainr/E2tg/_build/latest?definitionId=2&branchName=anime)

## With HandBrakeCLI support

### Variables

___(For local/vps deployment rename [.env.sample](.env.sample) to .env and edit with your variable)___

---
Compulsory Variables | Explanation
:--------- | :---------------------------------------------
`APP_ID` `API_HASH` `BOT_TOKEN` | get the first two from *[Telegram.org](https://telegram.org)* and the third from *[@Botfather](https://t.me/botfather)*
`OWNER`    | input id Of allowed users with a space between each

Optional Variables | Explanation
:--------- | :---------------------------------------------
`THUMBNAIL` `ICON` | input telegraph link of a picture for use as Thumbnail, Watermark.
`FFMPEG` | input Your FFMPEG Code or Handbrake-cli code (after installing it)  with """{}""" as input and output. (Eg. __ffmpeg -i """{}""" -preset veryfast -vcodec libx265 -crf 27 """{}"""__) escape the " characters if you're deploying locally 
`TEMP_USERS` | Additional restricted users allowed to use the bot
`LOG_CHANNEL` | Input Log Group/Channel ID (bot must be an admin in target group or channel)
`DATABASE_URL` | input valid Mongodb Database Url
`FCHANNEL` `FCHANNEL_STATS` | Input Channel id where **only** the output video will get forwarded. For the 2nd variable input message id of a message in channel to be used as live status for encodes.
`ALLOW_ACTION` type=bool | Set to True or False depending on whether you want chat actions enabled for bot
`UPSTREAM_REPO` `UPSTREAM_BRANCH` | Input custom repo link and custom repo branch name, For use with the update function
   | *Note:* Update will fail if there are new modules or dependencies in bot. Redeploy if that happens 
---


### Anime branch 

__Customized To work Specifically For Animes!__

### Commands
---
```
start - Check If Bot Is Awake
restart -  Restart Bot 
update - Update bot 
nuke - ☢️ Nuke bot 
bash - /bash + command 
eval - Evaluate code
lock - prevent bot from encoding 
peval - same as eval but with pyrogram 
ping - Ping!
queue - List queue
encodequeue - List queue (parsed)
fix - Turn V2 On (With Message) or Off
get - Get Current ffmpeg code
set - Set custom ffmpeg code
reset - Reset default ffmpeg code
filter - Filter & stuff
vfilter - View filter
groupenc - Allow Encoding in Group Toggle 
delfilter - Delete filter
status - 🆕 Get bot's status
showthumb - 🖼️ Show Current Thumbnail
parse - Toggle Parsing with captions or Anilist
cancelall - ❌ Clear Cached Downloads & Queued Files
clear - Clear Queued Files
logs - Get Bot Logs
help - Get Detailed Help
```

### Features:
__(Coming Soon)__

### Source 

- **[An Heavily Modified Fork of Danish CompressorQueue](https://github.com/1Danish-00/CompressorQueue)**
