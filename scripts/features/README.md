This guide explains the different features the user can use to have a better developer experience

<br />

---

- [Auto-Update](#auto-update)

---

<br />

# Auto-Update

This Python program can manually update a neuron (miner or validator) when auto-update is not enabled.

It can be used as such

```bash
python3 scripts/features/auto_update.py --neuron miner --version 2.2.5
```

Options

- `--version` - Specify the version to update to.
- `--tag` - Specify the tag to update to.
- `--branch` - Specify the branch to update to.

Options for validator (only)

- `--database.host` - Host of the redis database, by default `localhost`.
- `--database.port` - Port of the redis database, by default `6379`.
- `--database.index` - Index of the redis database, by default `1`.
- `--database.redis_password` - Password of the redis database, use `$(sudo grep -Po '^requirepass \K.*' /etc/redis/redis.conf)` or `docker exec -it subvortex-redis /bin/sh -c "grep -Eo '^requirepass[[:space:]]+(.*)$' /etc/redis/redis.conf | awk '{print \$2}'"`
- `--database.redis_dump_path` - Directory where to store dumps, by default `/etc/redis/`.

Only one of these arguments can be used at a time.

The `--branch` argument is used by the SubVortex team during development, so please do not use it on the mainnet.
