FROM node:22.22.2-alpine

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
RUN apk add --no-cache sudo curl nano
RUN npm install pm2 -g npm@12

WORKDIR /pneumatic_frontend
ADD package-lock.json /pneumatic_frontend/package-lock.json
ADD package.json /pneumatic_frontend/package.json
RUN npm ci --legacy-peer-deps --ignore-scripts

ADD . /pneumatic_frontend/

# Build webpack bundle at image build time (env-independent since runtime config refactor)
ENV NODE_OPTIONS="--max-old-space-size=3072"
RUN npm run build-client:prod

CMD ["pm2-runtime", "start", "pm2.json"]
