# [BETA] [![pyLint](https://github.com/Nubuki-all/Tg-encoder/actions/workflows/pyLint.yml/badge.svg?branch=main)](https://github.com/Nubuki-all/Tg-encoder/actions/workflows/pyLint.yml)

## [Deprecated… Use v2 instead.]
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
`ENCODER` | Encoder's name/nickname to be included in captions can also contain encode info.
`FCHANNEL` `FCHANNEL_STATS` | Input Channel id where **only** the output video will get forwarded. For the 2nd variable input message id of a message in channel to be used as live status for encodes.
`EABF` type=bool | (Enable all beta features) Enable all beta (maybe unstable) features in bot. Turned on by default, set to false to turn off.
`ALWAYS_DEPLOY_LATEST` type=bool | When starting bot always pull latest code from upstream repo or default repo if none is given 
`ALLOW_ACTION` type=bool | Set to True or False depending on whether you want encoding chat actions enabled for bot
`UPSTREAM_REPO` `UPSTREAM_BRANCH` | Input custom repo link and custom repo branch name, For use with the update function
  . | *Note:* Update will fail if there are new modules or dependencies in bot. Redeploy if that happens 
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
l - pass uri link with a single file to dl with aria2c 
queue - List queue
fforward - Manually forward a message to FCHANNEL
v - Turn V2,3,4… On (With Message) or Off
get - Get Current ffmpeg code
set - Set custom ffmpeg code
reset - Reset default ffmpeg code
filter - Filter & stuff
vfilter - View filter
groupenc - Allow Encoding in Group Toggle 
delfilter - Delete filter
name - quick filter with anime_title
vname - get list of name filter
delname - delete name filter
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
