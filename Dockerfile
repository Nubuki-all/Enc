# Base Image 
FROM fedora:37
#FROM colserra/fedora37_wf
# 2nd docker image allows skipping step 2-3 & 5-6

# 1. Setup home directory, non interactive shell and timezone
RUN mkdir -p /bot /tgenc && chmod 777 /bot
WORKDIR /bot
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Africa/Lagos
ENV TERM=xterm

# 2. Install Dependencies
RUN dnf -qq -y update && dnf -qq -y install git aria2 bash xz wget curl pv jq python3-pip mediainfo psmisc procps-ng qbittorrent-nox && if [[ $(arch) == 'aarch64' ]]; then   dnf -qq -y install gcc python3-devel; fi && python3 -m pip install --upgrade pip setuptools

# 3. Install latest ffmpeg
RUN arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/64/) && \
    wget -q https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-linux${arch}-gpl-7.1.tar.xz && tar -xvf *xz && cp *7.1/bin/* /usr/bin && rm -rf *xz && rm -rf *7.1

# 4. Copy files from repo to home directory
COPY . .

# 5. Install python3 requirements
RUN pip3 install -r requirements.txt

# 6. cleanup for arm64
RUN if [[ $(arch) == 'aarch64' ]]; then   dnf -qq -y history undo last; fi && dnf clean all

# 7. Start bot
CMD ["bash","run.sh"]
