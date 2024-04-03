This guide provides step-by-step instructions for creating and restoring a dump in Redis. Redis is an open-source, in-memory data structure store used as a database, cache, and message broker. Dumps are a way to back up and restore data in Redis.

<br />

Table of Contents
---

- [Create a dump](#create-a-dump)
- [Restore a dump](#restore-a-dump)

<br />

## Creating a Redis Dump

To create a dump of your Redis database, follow these steps:

1. **Connect to Redis**: Open a terminal or command prompt and connect to your Redis instance using the `redis-cli` command:

   ```bash
   redis-cli -a $(sudo grep -Po '^requirepass \K.*' /etc/redis/redis.conf)
   ```

2. **Create the Dump**: Use the `SAVE` command to create a dump of the current database. This command saves the dataset to a file called `dump.rdb` in the Redis data directory.

   ```bash
   SAVE
   ```

3. **Create the Dump**: Exit redis environment

   ```bash
   exit
   ```

4. **Make a copy**: Copy the dump file `dump.rdb` in `/var/lib/redis` and make a copy of it

   ```bash
   sudo cp /var/lib/redis/dump.rdb /var/lib/redis/dump.bak.rdb
   ```

5. **Verify the Dump**: Check that the copy of the dump file (`dump.bak.rdb`) has been created in `/var/lib/redis`.
   ```bash
   ls /var/lib/redis
   ```

## Restoring a Redis Dump

To restore a dump in Redis, follow these steps:

1. **Stop the Redis Server**: If Redis is running, stop the Redis server:

   ```bash
   sudo systemctl stop redis-server.service
   ```

2. **Replace the Dump File**: Replace the existing `dump.rdb` file in the Redis data directory with the dump file you want to restore.

3. **Start the Redis Server**: Start the Redis server again.

   ```bash
   sudo systemctl start redis-server.service
   ```

4. **Verify the Restoration**: Connect to Redis using `redis-cli` and verify that the data has been restored correctly:

   ```bash
   redis-cli
   KEYS *
   ```

   This command will display all keys in the database, confirming that the restoration was successful.

## Additional Notes

- It's important to ensure that Redis is stopped before replacing the dump file to avoid data corruption.

For more information about Redis and its commands, refer to the [Redis Documentation](https://redis.io/documentation).