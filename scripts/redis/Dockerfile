FROM redis:7.2.4-alpine

ARG REDIS_PASSWORD
ENV REDIS_PASSWORD=$REDIS_PASSWORD

RUN mkdir /etc/redis/ && \
    mkdir /var/lib/redis/  && \
    mkdir /var/run/redis/

RUN chown -R redis:redis /etc/redis/ && \
    chown -R redis:redis /var/lib/redis/ && \
    chown redis:redis /var/run/redis

# Copy the entrypoint script into the image
COPY ./scripts/redis/entrypoint.sh /usr/local/bin/entrypoint.sh

# Set the script as the entrypoint
ENTRYPOINT ["entrypoint.sh"]

# Set the default command (which can be overridden)
CMD []