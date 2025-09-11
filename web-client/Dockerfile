FROM node:18-bookworm-slim

# Installation pm2
# pm2 image does not build in amd64/linux (debian) https://hub.docker.com/r/keymetrics/pm2/
# Install pm2 manually following instruction: https://pm2.io/docs/runtime/guide/installation/
RUN apt-get update
RUN apt-get install -y sudo curl nano
RUN npm install pm2 -g
EXPOSE 80 443 43554

# Web client build vars
ENV MCS_RUN_ENV=prod
ENV NODE_OPTIONS=--max-old-space-size=3072
ENV FRONTEND_URL=http://pneumatic.local
ENV FORM_DOMAIN=form.pneumatic.local
ENV BACKEND_PRIVATE_URL=http://pneumatic-nginx/
ENV BACKEND_URL=http://api.pneumatic.local/
ENV WSS_URL=wss://api.pneumatic.local/
ENV BILLING=yes
ENV CAPTCHA=no
ENV SIGNUP=yes
ENV SSO_AUTH=no
ENV GOOGLE_AUTH=no
ENV ANALYTICS=no
ENV MS_AUTH=no
ENV SENTRY_DSN=no

WORKDIR /pneumatic_frontend
ADD package-lock.json /pneumatic_frontend/package-lock.json
ADD package.json /pneumatic_frontend/package.json
RUN npm ci --legacy-peer-deps

ADD . /pneumatic_frontend/
RUN npm run build-client:prod
