This documentation explains how to rollout/rollback the new migration for redis.

<br />

---

- [Rollout](#rollout)
- [Rollback](#rollback)

---

<br />

> **IMPORTANT - GOOD PRACTICE** <br />
As soon as a migration is mentioned, whether it's a rollout or not, please ensure to back up your database. Refer to the [Backup guide](../dump.md) for detailed instructions on how to backup and restore your dump.

<br /> 

# Rollout

There is no rollout for this release.

<br /> 

# Rollback

This migration creates a new key `selection:<SS58_HOTKEY>` in redis, so we need to remove it if you decide to rollback.

To rollback this release, check you are in the **SubVortex** directory

```
cd $HOME/SubVortex
```

Then, execute

```
python3 ./scripts/migration/release-2.0.1/migration.py --run-type rollback
```

The script is performing a check to ensure that everything has been rolled back. You should see
```bash
2024-03-29 19:25:53.615 |       INFO       | Checking rollback...          
2024-03-29 19:25:53.616 |       INFO       | Rollback checked successfully
```

# Troubleshooting

If you have any issue please refer to the [Backup guide](../dump.md) and restore your backup!

