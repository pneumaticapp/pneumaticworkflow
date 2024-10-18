FROM keymetrics/pm2:18-alpine

ARG MAX_OLD_SPACE_SIZE=4096

ENV PROJECT_NAME "pneumatic_frontend"
ENV MCS_RUN_ENV=$MCS_RUN_ENV
ENV NODE_OPTIONS=--max-old-space-size=${MAX_OLD_SPACE_SIZE}

ENV BILLING=yes
ENV CAPTCHA=yes
ENV SIGNUP=yes
ENV SSO_AUTH=yes
ENV GOOGLE_AUTH=yes
ENV ANALYTICS=yes
ENV MS_AUTH=yes

RUN mkdir /${PROJECT_NAME}
WORKDIR /${PROJECT_NAME}
ADD package-lock.json /${PROJECT_NAME}/package-lock.json
ADD package.json /${PROJECT_NAME}/package.json
RUN npm ci --legacy-peer-deps

ADD . /${PROJECT_NAME}/
RUN npm run build-client:prod
