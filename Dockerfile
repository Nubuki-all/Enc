# Base Image 
FROM fedora:37

# Setup home directory, non interactive shell and timezone
RUN mkdir /bot /tgenc && chmod 777 /bot
WORKDIR /bot
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Africa/Lagos

# Install Dependencies
RUN yum -qq -y update && yum -qq -y install git aria2 bash xz wget curl pv jq python3-pip mediainfo && dnf -qq -y install procps-ng && python3 -m pip install --upgrade pip

# Install latest ffmpeg
RUN wget https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2023-03-23-14-03/ffmpeg-n6.0-11-g3980415627-linux64-gpl-6.0.tar.xz && tar -xvf *xz && cp *6.0/bin/* /usr/bin && rm -rf *xz && rm -rf *6.0

# Copy files from repo to home directory
COPY . .

# Install python3 requirements
RUN pip3 install -r requirements.txt

# Start bot
CMD ["bash","run.sh"]
