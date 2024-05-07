This guide provides step-by-step instructions for the release 2.2.3.

Previous Release: 2.2.2

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
   git checkout tags/v2.2.3
   ```

   Finally, install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Delete validator**: Remove your validator

   ```bash
   pm2 delete validator-7
   ```

   Use `pm2 show validator-7` to get the list of arguments you were using to be able to restore them in the step 3.

3. **Start validator in auto-upgrade mode**: Start the validator by running in **Subvortex**

   ```bash
   pm2 start neurons/validator.py -f \
      --name validator-7 \
      --interpreter python3 -- \
      --netuid 7 \
      --wallet.name $WALLET_NAME \
      --wallet.hotkey $HOTKEY_NAME \
      --subtensor.chain_endpoint ws://$IP:9944 \
      --logging.debug  \
      --auto-update
   ```

   Replace **$WALLET_NAME**, **$HOTKEY_NAME** and **$IP** by the expected value.
   If you had other arguments, please add them!

   > IMPORTANT <br />
   > Do not forget to provide the `--auto-update` argument.

   > IMPORTANT <br />
   > Use wandb without overriding the default value, as it will enable the Subvortex team to monitor the version of the validators and take action if necessary.

4. **Check logs**: Check the validator logs to see if you see some `New Block`
   ```bash
   pm2 logs validator-7
   ```

<br />

## Rollback Process <a id="validator-rollback-process"></a>

If any issues arise during or after the rollout, follow these steps to perform a rollback:

1. **Downgrade Subnet**: Checkout the previous release tag

   ```bash
   git checkout tags/v2.2.2
   ```

   Then, install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Delete validator**: Remove your validator

   ```bash
   pm2 delete validator-7
   ```

   Use `pm2 show validator-7` to get the list of arguments you were using to be able to restore them in the step 3.

3. **Start validator**: Start the validator by running in **Subvortex**

   ```bash
   pm2 start neurons/validator.py -f \
      --name validator-7 \
      --interpreter python3 -- \
      --netuid 7 \
      --wallet.name $WALLET_NAME \
      --wallet.hotkey $HOTKEY_NAME \
      --subtensor.chain_endpoint ws://$IP:9944 \
      --logging.debug
   ```

   Replace **$WALLET_NAME**, **$HOTKEY_NAME** and **$IP** by the expected value.
   If you had other arguments, please add them!

   > IMPORTANT <br />
   > Do not forget to remove the `--auto-update` argument.

4. **Check logs**: Check the validator logs to see if you see some `New Block`
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
   git checkout tags/v2.2.3
   ```

   Finally, install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Delete miner**: Remove your miner

   ```bash
   pm2 delete miner-7
   ```

   Use `pm2 show miner-7` to get the list of arguments you were using to be able to restore them in the step 3.

3. **Start validator in auto-upgrade mode**: Start the miner by running in **Subvortex**

   ```bash
   pm2 start neurons/miner.py -f \
      --name miner-7 \
      --interpreter python3 -- \
      --netuid 7 \
      --wallet.name $WALLET_NAME \
      --wallet.hotkey $HOTKEY_NAME \
      --logging.debug  \
      --auto-update
   ```

   Replace **$WALLET_NAME**, **$HOTKEY_NAME** and **$IP** by the expected value.
   If you had other arguments, please add them!

   > IMPORTANT <br />
   > Do not forget to provide the `--auto-update` argument.

4. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-7
   ```

## Rollback Process <a id="miner-rollback-process"></a>

1. **Downgrade Subnet**: Checkout the previous release tag

   ```bash
   git checkout tags/v2.2.2
   ```

   Then, install the dependencies

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Delete miner**: Remove your miner

   ```bash
   pm2 delete miner-7
   ```

   Use `pm2 show miner-7` to get the list of arguments you were using to be able to restore them in the step 3.

3. **Start miner**: Start the miner by running in **Subvortex**

   ```bash
   pm2 start neurons/miner.py -f \
      --name miner-7 \
      --interpreter python3 -- \
      --netuid 7 \
      --wallet.name $WALLET_NAME \
      --wallet.hotkey $HOTKEY_NAME \
      --logging.debug
   ```

   Replace **$WALLET_NAME**, **$HOTKEY_NAME** and **$IP** by the expected value.
   If you had other arguments, please add them!

   > IMPORTANT <br />
   > Do not forget to remove the `--auto-update` argument

4. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-7
   ```

<br />

# Additional Resources

For any further assistance or inquiries, please contact [**SubVortex Team**](https://discord.com/channels/799672011265015819/1215311984799653918)
