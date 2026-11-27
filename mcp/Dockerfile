FROM node:24-bookworm-slim

LABEL org.opencontainers.image.title="Pneumatic MCP server" \
      org.opencontainers.image.source="https://github.com/pneumaticapp/pneumaticworkflow/mcp" \
      org.opencontainers.image.url="https://www.pneumatic.app" \
      org.opencontainers.image.authors="support@pneumatic.app" \
      org.opencontainers.image.vendor="Pneumatic Software Inc." \
      org.opencontainers.image.documentation="https://github.com/pneumaticapp/pneumaticworkflow/wiki" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN apt-get update
RUN apt-get install -y sudo curl nano

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build && npm prune --omit=dev

CMD ["node", "dist/index.js"]
