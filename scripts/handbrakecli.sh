#!/bin/bash
# Configure these as needed
SRC=downloads
DEST=encode
DEST_EXT=mkv
HANDBRAKE_CLI=HandBrakeCLI
PRESET="Fast 480p30"
IFS=$(echo -en "\n\b")
# The script itself
for FILE in `ls $SRC`
do
filename=$(basename $FILE)
extension=${filename##*.}
filename=${filename%.*}
$HANDBRAKE_CLI -i $SRC/$FILE -o "$DEST/$filename [Encoded].$DEST_EXT"  -e x265 --encoder-preset slow  -q 30 -b 420 -X 852 -Y 480 -a "1,2" -E "aac" -6 stereo -B 32 -s "1,2,3,4,5,6,7" -S "[Telegram: @Rscommunity] [Unknown],[Telegram: @Rscommunity] [UNKNOWN| SDH]" -A "[Telegram: @RsTvSeries] ➟" --ssa-file "Input.ass" --ssa-burn=1
done
