FROM alpine:latest

# Install dependencies including the Docker CLI
RUN apk add --no-cache \
    bash \
    curl \
    py3-pip \
    docker-cli \
    openrc \
    busybox-extras \
    util-linux \
    shadow \
    tzdata \
    && rm -rf /var/cache/apk/*

# Copy your crontab file
COPY crontab /etc/crontabs/root

# Run cron in foreground
CMD ["crond", "-f", "-l", "2"]
