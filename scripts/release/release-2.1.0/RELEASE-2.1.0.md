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

2. **Stop validator**: Stop your validator. We **HAVE TO** stop it because there is a redis migration.

   ```bash
   pm2 stop validator-92
   ```

   Check you have **stopped** in the status as shown below

   ```
   ┌────┬─────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
   │ id │ name            │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
   ├────┼─────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
   │ 0  │ validator-92    │ default     │ N/A     │ fork    │ 0        │ 0      │ 1    │ stopped   │ 0%       │ 0b       │ root     │ disabled │
   └────┴─────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
   ```

3. **Upgrade Subnet**: Check if you are on main or on a tag

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
   > The \* tell you your active branch. It has to be on the tag or on the main branch.

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

4. **Wandb login**: Login do wandb with the api key by following the [Wandb guide](../../../docs/wandb/wandb.md#installation) section installation.

5. **Rollout Redis**: Rollout redis by running in **SubVortex** directory

   ```bash
   python3 ./scripts/release/release-2.1.0/migration.py
   ```

   You will see

   ```bash
   2024-03-30 13:12:25.887 |       INFO       | Loading database from localhost:6379
   2024-03-30 13:12:25.899 |       INFO       | Rollout starting
   2024-03-30 13:12:25.932 |       INFO       | Rollout done
   2024-03-30 13:12:25.933 |       INFO       | Checking rollout...
   2024-03-30 13:12:25.940 |       INFO       | Rollout checked successfully
   ```

6. **Restart validator**: Restart your validator to take the new version and use wandb
   If you were not using wandb before, please delete the validator

   ```bash
   pm2 delete validator-92
   ```

   Then, run the following command by chaing all the variable **$XXX**

   ```bash
   pm2 start neurons/validator.py \
    --name validator-92 \
    --interpreter python3 -- \
    --netuid 92 \
    --wallet.name $WALLET_NAME \
    --wallet.hotkey $HOTKEY_NAME \
    --subtensor.chain_endpoint ws://$SUBTENSOR_IP:9944 \
    --logging.debug
   ```

   If you were using wandb before, please restart the validator

   ```bash
   pm2 restart validator-92
   ```

7. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-92
   ```

<br />

## Rollback Process <a id="validator-rollback-process"></a>

If any issues arise during or after the rollout, follow these steps to perform a rollback:

1. **Stop validator**: Stop your validator. We **HAVE TO** stop it because there is a redis migration.

   ```bash
   pm2 stop validator-92
   ```

   Check you have **stopped** in the status as shown below

   ```
   ┌────┬─────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
   │ id │ name            │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
   ├────┼─────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
   │ 0  │ validator-92    │ default     │ N/A     │ fork    │ 0        │ 0      │ 1    │ stopped   │ 0%       │ 0b       │ root     │ disabled │
   └────┴─────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
   ```

2. **Rollback Redis**: Rollback redis by running in **SubVortex** directory

   ```bash
   python3 ./scripts/release/release-2.1.0/migration.py --run-type rollback
   ```

   You should see

   ```bash
   2024-03-30 13:12:20.909 |       INFO       | Loading database from localhost:6379
   2024-03-30 13:12:20.920 |       INFO       | Rollback starting
   2024-03-30 13:12:20.961 |       INFO       | Rollback done
   2024-03-30 13:12:20.961 |       INFO       | Checking rollback...
   2024-03-30 13:12:20.962 |       INFO       | Rollback checked successfully
   ```

   If any issue, restore your backup database using the [Backup Guide](../../migrations/backup.md#restore-a-dump).

3. **Downgrade Subnet**: Get the tags

   ```bash
   git fetch --tags
   ```

   Check tag v2.0.0 exists

   ```bash
   git tag
   ```

   Checkout the tag

   ```bash
   git checkout tags/v2.0.0
   ```

   you will see

   ```
   Note: switching to 'tags/v2.0.0'.

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

4. **Restart validator**: Restart your validator to take the old version

   ```bash
   pm2 restart validator-92
   ```

   If you have any issue with wandb, please check you are logged in

   ```bash
   wandb login
   ```

   You have to see something like

   ```bash
   wandb: Currently logged in as: eclipsevortext. Use `wandb login --relogin` to force relogin
   ```

   If not, please login by following the [Wandb guide](../../../docs/wandb/wandb.md)

5. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-92
   ```

<br />

# Miner

## Rollout Process <a id="miner-rollout-process"></a>

1. **Upgrade Subnet**: Check if you are on main or on a tag

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
   > The \* tell you your active branch. It has to be on the tag or on the main branch.

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

2. **Restart miner**: Restart your miner to take the new version

   ```bash
   pm2 restart miner-92
   ```

3. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-92
   ```

## Rollback Process <a id="miner-rollback-process"></a>

If any issues arise during or after the rollout, follow these steps to perform a rollback:

1. **Downgrade Subnet**: Get the tags

   ```bash
   git fetch --tags
   ```

   Check tag v2.0.0 exists

   ```bash
   git tag
   ```

   Checkout the tag

   ```bash
   git checkout tags/v2.0.0
   ```

   you will see

   ```
   Note: switching to 'tags/v2.0.0'.

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

2. **Restart miner**: Restart your miner to take the old version

   ```bash
   pm2 restart miner-92
   ```

3. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-92
   ```

<br />

# Additional Resources

- [Backup Guide](../../redis/docs/redis-backup.md): Detailed instructions for backing up and restoring your database.

<br />

For any further assistance or inquiries, please contact [**SubVortex Team**](https://discord.com/channels/799672011265015819/1215311984799653918)