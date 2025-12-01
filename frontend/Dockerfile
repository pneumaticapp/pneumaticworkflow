FROM node:18-bookworm-slim

LABEL org.opencontainers.image.title="Pneumatic web client" \
      org.opencontainers.image.source="https://github.com/pneumaticapp/pneumaticworkflow/frontend" \
      org.opencontainers.image.url="https://www.pneumatic.app" \
      org.opencontainers.image.authors="support@pneumatic.app" \
      org.opencontainers.image.vendor="Pneumatic Software Inc." \
      org.opencontainers.image.documentation="https://github.com/pneumaticapp/pneumaticworkflow/wiki" \
      org.opencontainers.image.licenses="Apache-2.0"

ARG MCS_RUN_ENV="prod"
ARG NODE_OPTIONS="--max-old-space-size=3072"

ARG BACKEND_PRIVATE_URL="http://pneumatic-nginx/"
ARG BACKEND_URL="http://localhost:8001/"
ARG WSS_URL="ws://localhost:8001/"
ARG FORM_DOMAIN="form.localhost"

ARG LANGUAGE_CODE="en"
ARG CAPTCHA="no"
ARG ANALYTICS="no"
ARG BILLING="no"
ARG SIGNUP="yes"
ARG MS_AUTH="no"
ARG GOOGLE_AUTH="no"
ARG SSO_AUTH="no"
ARG SSO_PROVIDER
ARG AI="no"
ARG AI_PROVIDER
ARG PUSH="no"
ARG PUSH_PROVIDER
ARG STORAGE="no"
ARG STORAGE_PROVIDER

ARG SENTRY_DSN
ARG RECAPTCHA_SECRET
ARG FIREBASE_VAPID_KEY
ARG FIREBASE_API_KEY
ARG FIREBASE_AUTH_DOMAIN
ARG FIREBASE_PROJECT_ID
ARG FIREBASE_STORAGE_BUCKET
ARG FIREBASE_SENDER_ID
ARG FIREBASE_APP_ID
ARG FIREBASE_MEASUREMENT_ID


ENV MCS_RUN_ENV=${MCS_RUN_ENV}
ENV NODE_OPTIONS=${NODE_OPTIONS}
ENV BACKEND_PRIVATE_URL=${BACKEND_PRIVATE_URL}
ENV BACKEND_URL=${BACKEND_URL}
ENV WSS_URL=${WSS_URL}
ENV FORM_DOMAIN=${FORM_DOMAIN}

ENV LANGUAGE_CODE=${LANGUAGE_CODE}
ENV CAPTCHA=${CAPTCHA}
ENV ANALYTICS=${ANALYTICS}
ENV BILLING=${BILLING}
ENV SIGNUP=${SIGNUP}
ENV MS_AUTH=${MS_AUTH}
ENV GOOGLE_AUTH=${GOOGLE_AUTH}
ENV SSO_AUTH=${SSO_AUTH}
ENV SSO_PROVIDER=${SSO_PROVIDER}
ENV AI=${AI}
ENV AI_PROVIDER=${AI_PROVIDER}
ENV PUSH=${PUSH}
ENV PUSH_PROVIDER=${PUSH_PROVIDER}
ENV STORAGE=${STORAGE}
ENV STORAGE_PROVIDER=${STORAGE_PROVIDER}

ENV SENTRY_DSN=${SENTRY_DSN}
ENV RECAPTCHA_SECRET=${RECAPTCHA_SECRET}
ENV FIREBASE_VAPID_KEY=${FIREBASE_VAPID_KEY}
ENV FIREBASE_API_KEY=${FIREBASE_API_KEY}
ENV FIREBASE_AUTH_DOMAIN=${FIREBASE_AUTH_DOMAIN}
ENV FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
ENV FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET}
ENV FIREBASE_SENDER_ID=${FIREBASE_SENDER_ID}
ENV FIREBASE_APP_ID=${FIREBASE_APP_ID}
ENV FIREBASE_MEASUREMENT_ID=${FIREBASE_MEASUREMENT_ID}

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
