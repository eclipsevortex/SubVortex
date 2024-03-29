This documentation explains how to rollout/rollback the new migration for redis.

<br />

---

- [Rollout](#rollout)
- [Rollback](#rollback)

---

<br />

# Rollout

There is no rollout for this release.

# Rollback

This release creates a new key `selection:<SS58_HOTKEY>` in redis, so we need to remove it if you decide to rollback.

To rollback this release, check you are in the **SubVortex** directory

```
cd $HOME/SubVortex
```

Then, execute

```
python3 ./scripts/migration/release-2.0.1/migration.py --run-type rollback
```