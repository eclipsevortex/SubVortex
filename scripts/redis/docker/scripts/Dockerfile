FROM redis:7.2.4-alpine

ARG REDIS_CONF
ENV REDIS_CONF=$REDIS_CONF

RUN mkdir /etc/redis/ && \
    mkdir /var/lib/redis/  && \
    mkdir /var/run/redis/

COPY $REDIS_CONF /etc/redis/

RUN chown -R redis:redis /etc/redis/ && \
    chown -R redis:redis /var/lib/redis/ && \
    chown redis:redis /var/run/redis