#!/bin/bash

RED='\033[0;31m\e[1m'
NC='\033[0m'
GREEN='\e[32m\e[1m'

# Check if python3 is installed.
if which python3 >/dev/null; then
    echo -e "${GREEN}python3 is installed…${NC}"
else
    echo -e "${RED}python3 not is installed.\nAborting…${NC}"
    exit 1
fi

# Check the Linux distribution
if grep -qi "fedora" /etc/os-release; then
    # Install the package on Fedora using yum
    echo -e "${GREEN} Fedora Detected!${NC}"
    echo -e "${GREEN}Downloading and installing system dependencies required to run bot…${NC}"
    sleep 2
    if which sudo >/dev/null; then
        echo -e "${GREEN}sudo is installed\nInstalling other requirements….${NC}"
    else
        echo -e "${GREEN}sudo is not installed\nInstalling alongside other requirements…${NC}"
        yum -qq -y update && yum -qq -y sudo
    fi
    sleep 2
    sudo yum -qq -y update && sudo yum -qq -y install git aria2 bash xz wget curl pv jq python3-pip mediainfo procps-ng qbittorrent-nox

elif grep -qi "ubuntu\|debian" /etc/os-release; then
    # Install the package on Ubuntu or Debian using apt
    #remove the '#' from line 37 if you want handbrake-cli support
    echo -e "${GREEN}Apt package manger detected!${NC}"
    echo -e "${GREEN}Downloading and installing system dependencies required to run bot…${NC}"
    sleep 2
    if which sudo >/dev/null; then
        echo -e "${GREEN}sudo is installed.\nInstalling other requirements…${NC}"
    else
        echo -e "${GREEN}sudo is not installed\nInstalling alongside other requirements…${NC}"
        apt -y -qq update && apt install sudo -y
    fi
    sleep 2
    sudo apt -y -qq update && sudo apt -y -qq install -y git wget curl aria2 pv jq python3-pip mediainfo qbittorrent-nox 
    #sudo apt -qq install handbrake-cli


else
    # Unsupported distribution
    echo -e "${RED}Unsupported Linux distribution.${NC}"
    echo -e "${RED}Exiting now…${NC}"
    exit 1
fi

sleep 3

# Install ffmpeg
if which ffmpeg >/dev/null; then
    echo -e "${GREEN}ffmpeg is installed.\nProceeding…${NC}"
else
    echo -e "${GREEN}ffmpeg is not installed.${NC}"
    echo -e "${GREEN}Downloading and installing latest ffmpeg…${NC}"
    wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.0-latest-linux64-gpl-6.0.tar.xz && tar -xvf *xz && cp *6.0/bin/* /usr/bin
    echo -e "${GREEN}Cleaning up…${NC}"
    rm -rf *xz && rm -rf *6.0
fi

sleep 2

# Install Python3 requirements
echo -e "${GREEN}Installing (using venv) python dependencies required to run bot…${NC}"
python3 -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt

sleep 2

# Starting bot
echo -e "${GREEN}Starting bot…${NC}"
python3 update.py && python3 -m bot