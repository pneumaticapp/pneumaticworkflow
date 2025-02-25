FROM keymetrics/pm2:18-alpine

# Build vars
ENV MCS_RUN_ENV=prod
ENV NODE_OPTIONS=--max-old-space-size=3072
ENV FRONTEND_URL=http://pneumatic.local
ENV FORM_DOMAIN=form.pneumatic.local
ENV BACKEND_PRIVATE_URL=http://pneumatic-nginx/
ENV BACKEND_URL=http://api.pneumatic.local/
ENV WSS_URL=wss://api.pneumatic.local/
ENV BILLING=no
ENV CAPTCHA=no
ENV SIGNUP=yes
ENV SSO_AUTH=no
ENV GOOGLE_AUTH=no
ENV ANALYTICS=no
ENV MS_AUTH=no
ENV SENTRY_DSN=

RUN apk add curl nano bash

RUN mkdir /pneumatic_frontend
WORKDIR /pneumatic_frontend
ADD package-lock.json /pneumatic_frontend/package-lock.json
ADD package.json /pneumatic_frontend/package.json
RUN npm ci --legacy-peer-deps

ADD . /pneumatic_frontend/
RUN npm run build-client:prod
