This guide provides step-by-step instructions for the release 2.1.0.

Previous Release: 2.0.0

<br />

---

- [Validator](#validators)
  - [Rollout Process](#validator-rollout-process)
  - [Rollback Process](#validator-rollback-process)
- [Miner](#miner)
  - [Rollout Process](#miner-rollout-process)
  - [Rollback Process](#miner-rollback-process)
- [Additional Resources](#additional-resources)

---

<br />

# Validator

## Rollout Process <a id="validator-rollout-process"></a>

1. **Backup Database**: Before starting the rollout process, backup your database using the [Backup Guide](../../redis/docs/redis-backup.md#create-a-dump).

2. **Upgrade Subnet**: Check if you are on main or on a tag

   ```bash
   git branch -vvv
   ```

   You will see something similar

   ```bash
   # If you are on a tag
   * (HEAD detached at v0.2.4)  d6e233a Merge pull request #13 from eclipsevortex/release/0.2.4

   # If you are on main
   * main                       13e555e [origin/main] Merge pull request #19 from eclipsevortex/release/2.0.0
   ```

   > IMPORTANT <br />
   > The \* tell you your active branch. It has to be hear on the tag on the main branch.

   If you are on a tag branch, checkout main

   ```bash
   git checkout main
   ```

   Otherwise/Then, get the latest version of the subnet

   ```bash
   git pull
   ```

   Then, install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Restart validator**: Restart your validator to take the new version into the new version

   ```bash
   pm2 restart validator-92
   ```

4. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-92
   ```

<br />

## Rollback Process <a id="validator-rollback-process"></a>

If any issues arise during or after the rollout, follow these steps to perform a rollback:

1. **Rollback Database**: Rollback the database by running in **SubVortex** directory

   ```bash
   python3 ./scripts/migrations/release-2.1.0/migration.py --run-type rollback
   ```

   You should see

   ```bash
    2024-03-29 22:08:27.867 |       INFO       | Loading database from localhost:6379
    2024-03-29 22:08:27.901 |       INFO       | Rollback starting
    2024-03-29 22:08:27.907 |       INFO       | Rollback done
    2024-03-29 22:08:27.908 |       INFO       | Checking rollback...
    2024-03-29 22:08:27.910 |       INFO       | Rollback checked successfully
   ```

   If any issue, restore your backup database using the [Backup Guide](../../migrations/backup.md#restore-a-dump).

2. **Downgrade Subnet**: Get the tags

   ```bash
   git fetch --tags
   ```

   Check tag v2.0.0 exist

   ```bash
   git tag
   ```

   Checkout the tag

   ```bash
   git checkout tags/v2.0.0
   ```

   you will see

   ```
   Note: switching to 'tags/v0.2.4'.

   You are in 'detached HEAD' state. You can look around, make experimental
   changes and commit them, and you can discard any commits you make in this
   state without impacting any branches by switching back to a branch.

   If you want to create a new branch to retain commits you create, you may
   do so (now or later) by using -c with the switch command. Example:

   git switch -c <new-branch-name>

   Or undo this operation with:

   git switch -

   Turn off this advice by setting config variable advice.detachedHead to false

   HEAD is now at d6e233a Merge pull request #13 from eclipsevortex/release/0.2.4
   ```

   Then install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Restart validator**: Restart your validator to take the new version into the new version

   ```bash
   pm2 restart validator-92
   ```

4. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs v
   ```

<br />

# Miner

## Rollout Process <a id="miner-rollout-process"></a>

There is no rollout for miners.

## Rollback Process <a id="miner-rollback-process"></a>

There is no rollback for miners.

<br />

# Additional Resources

- [Backup Guide](../../redis/docs/redis-backup.md): Detailed instructions for backing up and restoring your database.

<br />

For any further assistance or inquiries, please contact [**SubVortex Team**](https://discord.com/channels/799672011265015819/1215311984799653918)
