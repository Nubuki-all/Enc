#!/bin/bash
#remove the '#' from line 4 if you want handbrake-cli support 
apt -qq update && apt -qq install -y git wget pv jq python3-dev ffmpeg mediainfo
#apt -qq install handbrake-cli
pip3 install -r requirements.txt
