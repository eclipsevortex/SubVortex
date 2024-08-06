This guide provides step-by-step instructions for the release 2.2.6.

Previous Release: 2.2.5

<br />

---

- [Prerequisites](#prerequisites)
- [Validator](#validators)
  - [Rollout Process](#validator-rollout-process)
  - [Rollback Process](#validator-rollback-process)
- [Miner](#miner)
  - [Rollout Process](#miner-rollout-process)
  - [Rollback Process](#miner-rollback-process)
  - [Activate Firewall](#activate-firewall)
  - [Deactivate Firewall](#deactivate-firewall)
- [Additional Resources](#additional-resources)
- [Troubleshooting](#troubleshooting)

---

<br />

# Prerequisites

Before installing the new release using one of the two possible methods, some packages need to be installed as prerequisites.

```bash
./scripts/os/os_setup.sh -t miner
```

For validator, please use the same command line above as the requirements for now is common for miners and validators.


# Validator

## Rollout Process <a id="validator-rollout-process"></a>

1. **Upgrade Subnet**: Fetch the remote tags

   ```bash
   git fetch --tags --force
   ```

   Then, checkout the new release tag

   ```bash
   git checkout tags/v2.2.6
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
   git checkout tags/v2.2.5
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
   git checkout tags/v2.2.6
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

4. **Activate firewall**: refer to the section [Activate Firewall](#activate-firewall)

## Rollback Process <a id="miner-rollback-process"></a>

1. **Deacivate firewall**: refer to the section [Deactivate Firewall](#deactivate-firewall)

2. **Downgrade Subnet**: Checkout the previous release tag

   ```bash
   git checkout tags/v2.2.5
   ```

   Then, install the dependencies

   ```bash
   pip install --upgrade SubVortex
   pip install -e .
   ```

3. **Restart miner**: Restart your miner to take the old version

   ```bash
   pm2 restart miner-7
   ```

4. **Check logs**: Check the miner logs to see if you see some `New Block`
   ```bash
   pm2 logs miner-7
   ```

<br />

## Activate Firewall

The firewall is available only for Linux. For window and macos, it will be available in a future release.

> IMPORTANT <br />
> Modifying iptables rules can block access to your machine, potentially leaving you with no choice but to reinstall your VPS.
> Please be careful when managing iptables. We recommend using our scripts on a testnet VPS first.

> IMPORTANT <br />
> Please ensure your SSH port is set to 22, as this is the port we will allow. If you do not restore the default setting before starting the installation, you may lose access to your machine.

As pre-requisite, some packages need to be installed first

```bash
./scripts/os/os_setup.sh -t miner
```

Then, activate the firewall

```bash
python3 scripts/firewall/firewall_activate.py --process.name MINER_NAME
```

Options

- `--process.name` - name of the miner used by pm2.
- `--firewall.interface` - interface the firewall will listen traffic from. By default, it is `eth0`
- `--firewall.config` - Path to the firewall configuration file, default is `firewall.json`.
- `--sse.firewall.ip` - IP address of the firewall UI consumer to allow traffic only from that source.

> IMPORTANT <br />
> If you do not know your interface, you can use `tcpdump` in order see the interface. You should see at the beginning something like `listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes`

Replace `MINER_NAME` by the name of your miner.

Check the process arguments

```bash
pm2 show MINER_NAME
```

You should see something like

```bash
script args       │ --netuid 7 --subtensor.network local --wallet.name miner --wallet.hotkey default --logging.debug --firewall.on
```

Be sure you do **HAVE** the argument `--firewall.on`

Check the miner log

```bash
pm2 log MINER_NAME
```

You should see some firewall logs such as

```bash
12|miner-7  | 2024-06-24 19:02:32.133 |      DEBUG       |  - Starting firewall on interface eth0 -
```

Check the iptables

```bash
sudo iptables -n -v -L INPUT
```

You should see these rules

```bash
Chain INPUT (policy DROP 108K packets, 23M bytes)
 pkts bytes target     prot opt in     out     source               destination
  52M   22G ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0
1159K  139M ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22
  799 37952 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:443
18663   18M ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:443
  753 37575 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:80
13118 1616K ACCEPT     udp  --  *      *       0.0.0.0/0            0.0.0.0/0            udp spt:53
92006   23M NFQUEUE    tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:8091 NFQUEUE num 1
78210 4908K NFQUEUE    tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:9944 NFQUEUE num 2
   37  1840 NFQUEUE    tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:9933 NFQUEUE num 3
  37M 2620M NFQUEUE    tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:30333 NFQUEUE num 4
 736M   59G ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp spt:30333
```

## Deactivate Firewall

The firewall is available only for Linux. For window and macos, it will be available in a future release.

> IMPORTANT <br />
> Modifying iptables rules can block access to your machine, potentially leaving you with no choice but to reinstall your VPS.
> Please be careful when managing iptables. We recommend using our scripts on a testnet VPS first.

> IMPORTANT <br />
> Please ensure your SSH port is set to 22, as this is the port we will allow. If you do not restore the default setting before starting the installation, you may lose access to your machine.

To deactivate the firewall

```bash
python3 scripts/firewall/firewall_deactivate.py --process.name MINER_NAME
```

Replace `MINER_NAME` by the name of your miner.

Check the process arguments

```bash
pm2 show MINER_NAME
```

You should see something like

```bash
script args       │ --netuid 7 --subtensor.network local --wallet.name miner --wallet.hotkey default --logging.debug
```

Be sure you do **NOT HAVE** the argument `--firewall.on`

Check the iptables

```bash
sudo iptables -n -v -L INPUT
```

You should not see any rules mentioning in the activation of the firewall, so you should see something

```bash
Chain INPUT (policy ACCEPT 15481 packets, 1415K bytes)
 pkts bytes target     prot opt in     out     source               destination
```

# Additional Resources

For any further assistance or inquiries, please contact [**SubVortex Team**](https://discord.com/channels/799672011265015819/1215311984799653918)
