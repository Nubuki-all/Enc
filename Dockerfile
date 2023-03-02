#FROM python:3.9.2-slim-buster
FROM fedora:37
RUN mkdir /bot && chmod 777 /bot
WORKDIR /bot
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Africa/Lagos
RUN yum -qq -y update && yum -qq -y install git aria2 bash xz wget curl pv jq python3-pip mediainfo && dnf -qq -y install procps-ng && python3 -m pip install --upgrade pip
RUN wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n5.1-latest-linux64-gpl-5.1.tar.xz && tar -xvf *xz && cp *5.1/bin/* /usr/bin && rm -rf *xz && rm -rf *5.1
COPY . .
RUN pip3 install -r requirements.txt
CMD ["bash","run.sh"]
