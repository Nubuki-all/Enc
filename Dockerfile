# Base Image 
FROM fedora:37

# Setup home directory, non interactive shell and timezone
RUN mkdir /bot && chmod 777 /bot && /tgenc
WORKDIR /bot
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Africa/Lagos

# Install Dependencies
RUN yum -qq -y update && yum -qq -y install git aria2 bash xz wget curl pv jq python3-pip mediainfo && dnf -qq -y install procps-ng && python3 -m pip install --upgrade pip

# Install latest ffmpeg
RUN wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n5.1-latest-linux64-gpl-5.1.tar.xz && tar -xvf *xz && cp *5.1/bin/* /usr/bin && rm -rf *xz && rm -rf *5.1

# Copy files from repo to home directory
COPY . .

# Install python3 requirements
RUN pip3 install -r requirements.txt

# Start bot
CMD ["bash","run.sh"]
