This guide provides step-by-step instructions for the release 2.2.4.

Previous Release: 2.2.3

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

1. **Upgrade Subnet**: Fetch the remote tags

   ```bash
   git fetch --tags --force
   ```

   Then, checkout the new release tag

   ```bash
   git checkout tags/v2.2.4
   ```

   Finally, install the dependencies

   ```bash
   pip install --upgrade SubVortex
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

1. **Downgrade Subnet**: Checkout the previous release tag

   ```bash
   git checkout tags/v2.2.3
   ```

   Then, install the dependencies

   ```bash
   pip install --upgrade SubVortex
   pip install -e .
   ```

2. **Restart validator**: Restart your validator to take the old version

   ```bash
   pm2 restart validator-7
   ```

3. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-7
   ```

<br />

# Miner

## Rollout Process <a id="miner-rollout-process"></a>

1. **Upgrade Subnet**: Fetch the remote tags

   ```bash
   git fetch --tags --force
   ```

   Then, checkout the new release tag

   ```bash
   git checkout tags/v2.2.4
   ```

   Finally, install the dependencies

   ```bash
   pip install --upgrade SubVortex
   pip install -e .
   ```

2. **Restart miner**: Restart your miner to take the new version

   ```bash
   pm2 restart miner-7
   ```

3. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-7
   ```

## Rollback Process <a id="miner-rollback-process"></a>

1. **Downgrade Subnet**: Checkout the previous release tag

   ```bash
   git checkout tags/v2.2.3
   ```

   Then, install the dependencies

   ```bash
   pip install --upgrade SubVortex
   pip install -e .
   ```

2. **Restart miner**: Restart your miner to take the old version

   ```bash
   pm2 restart miner-7
   ```

3. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-7
   ```

<br />

# Additional Resources

For any further assistance or inquiries, please contact [**SubVortex Team**](https://discord.com/channels/799672011265015819/1215311984799653918)

# Troubleshooting

## Subtensor

If you have any issues with subtensor, please refer to the [Subtensor guide](../../subtensor/README.md)

## Miner

If the miner is blocked here (see this log for 10 seconds)

```
54|miner-9  | 2024-05-14 13:50:43.801 |       INFO       |  - Attaching forward functions to axon. -
54|miner-9  | 2024-05-14 13:50:43.810 |       INFO       |  - Serving axon Axon([::], 8091, 5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81, stopped, ['Synapse', 'Score']) on network: ws://127.0.0.1:9944 with netuid: 7 -
54|miner-9  | 2024-05-14 13:50:43.811 |      DEBUG       |  - Checking axon ... -
54|miner-9  | 2024-05-14 13:50:43.847 |      DEBUG       |  - Serving axon with: AxonInfo(5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81,155.133.26.129:8091) -> local:7 -
```

Just restart your miner

```
pm2 restart miner-7
```

We are still investigating the cause of the issue.