This guide provides step-by-step instructions for the release 2.2.2.

Previous Release: 2.2.1

<br />

---

- [Validator](#validators)
  - [Rollout Process](#validator-rollout-process)
  - [Rollback Process](#validator-rollback-process)
- [Miner](#miner)
  - [Rollout Process](#miner-rollout-process)
  - [Rollback Process](#miner-rollback-process)
- [Additional Resources](#additional-resources)
- [Troubleshooting](#troubleshooting)

---

<br />

# Validator

## Rollout Process <a id="validator-rollout-process"></a>

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

2. **Restart validator**: Restart your validator to take the new version

   ```bash
   pm2 restart validator-7
   ```

3. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-7
   ```

<br />

## Rollback Process <a id="validator-rollback-process"></a>

If any issues arise during or after the rollout, follow these steps to perform a rollback:

1. **Stop validator**: Stop your validator.

   ```bash
   pm2 stop validator-7
   ```

   Check you have **stopped** in the status as shown below

   ```
   ┌────┬─────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
   │ id │ name            │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
   ├────┼─────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
   │ 0  │ validator-7     │ default     │ N/A     │ fork    │ 0        │ 0      │ 1    │ stopped   │ 0%       │ 0b       │ root     │ disabled │
   └────┴─────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
   ```

2. **Downgrade Subnet**: Get the tags

   ```bash
   git fetch --tags
   ```

   Check tag v2.2.1 exists

   ```bash
   git tag
   ```

   Checkout the tag

   ```bash
   git checkout tags/v2.2.1
   ```

   you will see

   ```
   Note: switching to 'tags/v2.2.1'.

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

3. **Restart validator**: Restart your validator to take the old version

   ```bash
   pm2 restart validator-7
   ```

4. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-7
   ```

<br />

# Miner

## Rollout Process <a id="miner-rollout-process"></a>

There is no rollout

## Rollback Process <a id="miner-rollback-process"></a>

There is no rollback

<br />

# Additional Resources

For any further assistance or inquiries, please contact [**SubVortex Team**](https://discord.com/channels/799672011265015819/1215311984799653918)

# Troubleshooting

## Divergent branches

Sometimes when switchingg between branches, you may face the following message

```
hint: You have divergent branches and need to specify how to reconcile them.
hint: You can do so by running one of the following commands sometime before
hint: your next pull:
hint:
hint:   git config pull.rebase false  # merge (the default strategy)
hint:   git config pull.rebase true   # rebase
hint:   git config pull.ff only       # fast-forward only
hint:
hint: You can replace "git config" with "git config --global" to set a default
hint: preference for all repositories. You can also pass --rebase, --no-rebase,
hint: or --ff-only on the command line to override the configured default per
hint: invocation.
fatal: Need to specify how to reconcile divergent branches.
```

To resolve, let's check if you have at least another branch you can switch on

```bash
git branch -vvv
```

You have to see something like

```bash
  main          047e804 [origin/main] Merge pull request
* release/2.2.2 fc0868b [origin/release/2.2.2: ahead 1, behind 1] fix last details
```

The `*` tells you which branch is your active one. In my case, release/2.2.2 is my current one.

If there is no other branche available, please remove the SubrVortex directory and reinstall it by following the [Subnet guide](../../subnet/README.md)

If there are other branches, switch to it

```bash
git switch <BRANCH_NAME>
```

Delete the branch in issue

```bash
git delete -D <BRANCH_NAME>
```

Check the branch has been removed

```bash
git branch -vvv
```

You have to see something like

```bash
* main          047e804 [origin/main] Merge pull request
```

From there, you can restart from the point **Rollout process** or **Rollback process** of the Validator or Miner depending on the action you were doing originally.
