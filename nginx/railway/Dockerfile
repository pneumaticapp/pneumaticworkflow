FROM nginx:1.25.4-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint that extracts DNS resolver
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create temp directories for nginx to run as non-root friendly
RUN mkdir -p /var/www/html /tmp/nginx

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
