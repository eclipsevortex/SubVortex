cp /etc/redis/redis.conf /etc/redis/redis.conf.bak
export REDIS_PASSWORD=$(openssl rand -base64 20)
sed -i "/^# requirepass /c\requirepass $REDIS_PASSWORD" /etc/redis/redis.conf
sed -i "/^requirepass /c\requirepass $REDIS_PASSWORD" /etc/redis/redis.conf
systemctl restart redis-server.service
