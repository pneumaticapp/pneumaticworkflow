FROM node:18-bookworm-slim

LABEL org.opencontainers.image.title="Pneumatic web client" \
      org.opencontainers.image.source="https://github.com/pneumaticapp/pneumaticworkflow/frontend" \
      org.opencontainers.image.url="https://www.pneumatic.app" \
      org.opencontainers.image.authors="support@pneumatic.app" \
      org.opencontainers.image.vendor="Pneumatic Software Inc." \
      org.opencontainers.image.documentation="https://github.com/pneumaticapp/pneumaticworkflow/wiki" \
      org.opencontainers.image.licenses="Apache-2.0"

# Installation pm2
# pm2 image does not build in amd64/linux (debian) https://hub.docker.com/r/keymetrics/pm2/
# Install pm2 manually following instruction: https://pm2.io/docs/runtime/guide/installation/
RUN apt-get update
RUN apt-get install -y sudo curl nano
RUN npm install pm2 -g

WORKDIR /pneumatic_frontend
ADD package-lock.json /pneumatic_frontend/package-lock.json
ADD package.json /pneumatic_frontend/package.json
RUN npm ci --legacy-peer-deps

ADD . /pneumatic_frontend/
