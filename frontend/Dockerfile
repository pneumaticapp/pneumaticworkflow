FROM node:18-bookworm-slim

LABEL org.opencontainers.image.title="Pneumatic web client" \
      org.opencontainers.image.source="https://github.com/pneumaticapp/pneumaticworkflow/frontend" \
      org.opencontainers.image.url="https://www.pneumatic.app" \
      org.opencontainers.image.authors="support@pneumatic.app" \
      org.opencontainers.image.vendor="Pneumatic Software Inc." \
      org.opencontainers.image.documentation="https://github.com/pneumaticapp/pneumaticworkflow/wiki" \
      org.opencontainers.image.licenses="Apache-2.0"

ARG MCS_RUN_ENV="prod"
ARG NODE_OPTIONS="3072"
ARG BACKEND_PRIVATE_URL="http://pneumatic-nginx/"
ARG BACKEND_URL="http://localhost:8001/"
ARG WSS_URL="ws://localhost:8001/"
ARG FORM_DOMAIN="form.localhost"

ARG ENVIRONMENT="Production"
ARG LANGUAGE_CODE="en"
ARG CAPTCHA="no"
ARG ANALYTICS="no"
ARG BILLING="no"
ARG SIGNUP="yes"
ARG MS_AUTH="no"
ARG GOOGLE_AUTH="no"
ARG SSO_AUTH="no"
ARG EMAIL="no"
ARG EMAIL_PROVIDER
ARG AI="no"
ARG AI_PROVIDER
ARG PUSH="no"
ARG PUSH_PROVIDER
ARG STORAGE="no"
ARG STORAGE_PROVIDER

ENV MCS_RUN_ENV = $MCS_RUN_ENV
ENV NODE_OPTIONS = $NODE_OPTIONS
ENV BACKEND_PRIVATE_URL = $BACKEND_PRIVATE_URL
ENV BACKEND_URL = $BACKEND_URL
ENV WSS_URL = $WSS_URL
ENV FORM_DOMAIN = $FORM_DOMAIN

ENV ENVIRONMENT = $ENVIRONMENT
ENV LANGUAGE_CODE = $LANGUAGE_CODE
ENV CAPTCHA = $CAPTCHA
ENV ANALYTICS = $ANALYTICS
ENV BILLING = $BILLING
ENV SIGNUP = $SIGNUP
ENV MS_AUTH = $MS_AUTH
ENV GOOGLE_AUTH = $GOOGLE_AUTH
ENV SSO_AUTH = $SSO_AUTH
ENV EMAIL = $EMAIL
ENV EMAIL_PROVIDER = $EMAIL_PROVIDER
ENV AI = $AI
ENV AI_PROVIDER = $AI_PROVIDER
ENV PUSH = $PUSH
ENV PUSH_PROVIDER = $PUSH_PROVIDER
ENV STORAGE = $STORAGE
ENV STORAGE_PROVIDER = $STORAGE_PROVIDER

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
RUN npm run build-client:prod
