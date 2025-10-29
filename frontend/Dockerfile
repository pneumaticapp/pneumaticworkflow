FROM node:18-bookworm-slim

# Installation pm2
# pm2 image does not build in amd64/linux (debian) https://hub.docker.com/r/keymetrics/pm2/
# Install pm2 manually following instruction: https://pm2.io/docs/runtime/guide/installation/
RUN apt-get update
RUN apt-get install -y sudo curl nano
RUN npm install pm2 -g

WORKDIR /pneumatic_frontend
