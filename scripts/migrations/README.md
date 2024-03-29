## Backup
Please ensure you run the following to enter an authenticated session for redis:
```bash
redis-cli -a $REDIS_PASSWORD 
```

Then run save inside the session:

```bash
127.0.0.1:6379> SAVE
> OK

exit # exit the session to terminal
```

Finally, go to where the dump.rdb file is (`/var/lib/redis`` by default), and copy it as a backup **before** commencing the schema migration:

```bash
sudo cp /var/lib/redis/dump.rdb /var/lib/redis/dump.bak.rdb
```

> Shoutout to shr1ftyy for his step!