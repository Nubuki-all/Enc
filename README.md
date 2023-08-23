# [BETA] [![pyLint](https://github.com/Nubuki-all/Tg-encoder/actions/workflows/pyLint.yml/badge.svg?branch=main)](https://github.com/Nubuki-all/Tg-encoder/actions/workflows/pyLint.yml)

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
`LOGS_IN_CHANNEL` type=bool | Get error logs in log channel. Turned off by default, set to True to turn on.
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
start - check if bot is awake and get usage.
restart -  restart bot
update - update bot
nuke - ☢️ nuke bot
bash - /bash + command
eval - evaluate code
pause - prevent bot from encoding
peval - same as eval but with pyrogram
ping - ping!
l - add link to queue
queue - list queue
forward - manually forward a message to fchannel
v - turn v2,3,4… on (with message) or off
download - download a file or link to bot
upload - upload from a local directory or link
rename - rename a video file/link
mux - remux a file
get - get current ffmpeg code
set - set custom ffmpeg code
reset - reset default ffmpeg code
filter - filter & stuff
vfilter - view filter
groupenc - allow encoding in group toggle
delfilter - delete filter
name - quick filter with anime_title
vname - get list of name filter
delname - delete name filter
status - 🆕 get bot's status
showthumb - 🖼️ show current thumbnail
parse - toggle parsing with captions or anilist
groupenc - turn off/on encoding in groups
cancelall - ❌ clear cached downloads & queued files
clear - clear queued files
logs - get bot logs
help - same as start
```

### Features:
__(Coming Soon)__

### Source 

- **[An Heavily Modified Fork of Danish CompressorQueue](https://github.com/1Danish-00/CompressorQueue)**
