[Back to Main README](../../README.md)

Miners can be subjected to various attacks daily, such as DoS (Denial of Service) and DDoS (Distributed Denial of Service).

To protect miners, owners can enable the firewall feature available on all miners.

<br />

---

- [Prerequisites](#prerequisites)
- [Design](#design)
- [Installation](#installation)
  - [Manual installation](#manual-installation)
  - [Automatic installation](#automatic-installation)
- [Uninstallation](#uninstallation)
  - [Manual uninstallation](#manual-uninstallation)
  - [Automatic uninstallation](#automatic-uninstallation)
- [Rules](#rules)
  - [Static rules](#static-rules)
  - [Dynamic rules](#dynamic-rules)
    - [Hotkey Blacklisted Rule](#hotkey-blacklisted-rule)
    - [Wrong Synapse Rule](#wrong-synapse-rule)
    - [Old Validator Version Rule](#old-validator-version-rule)
    - [Denial of Service Rule](#denial-of-service-rule)
    - [Distributed Denial of Service Rule](#distributed-denial-of-service-rule)
  - [Custom rules](#custom-rules)
    - [Allow Rule](#allow-rule)
    - [Deny Rule](#deny-rule)
- [UI](#ui)
- [Recommendations](#recommendations)

---

<br />

# Prerequisites

Use the firewall if you are not on macOS or Windows, or on any VPS that does have `iptables` available. You can check if this command-line interface (CLI) exists by running:

```bash
type iptables
```

You should see something as

```bash
iptables is hashed (/usr/sbin/iptables)
```

In the future, we will try to add support for other firewall CLIs to cover macOS, Windows, and any other types of operating systems.

<br />

# Design

For SubVortex, we want our miners to become a firewall where all traffic coming in the VPS can go through the miner first which can decide to allow or deny it based on some rules.

The firewall loads its dynamic rules from the json file called `firewall.json`. This file can be updated and reloaded without restarting the miner.

The firewall maintain a njson file (`firewall-events.json`) that will contains all the packets received in order to be used by the UI and the firewall itself to make the right decision for future packets based on the defined rules.

The filewall will be automatically cleaned by removing any packets that belong to a request for which a SYNC packet is received before the defined time window. This time window is determined as the maximum between the time window specified in the rules (e.g., DoS, DDoS, etc.) and the default time window, which is 1 minute.

If a request within the time window is neither accepted nor denied, we keep the last request, even if it is outside the time window, as decisions are based on the current request and the previous one.

Cleaning the file this way helps prevent it from becoming too large, which could negatively impact the machine's performance.

In addition to storing each packet in the firewall nsjson file, we broadcast them via an event stream to any subscribers. You can use the UI to view these packets. Please see the [UI Guide](../../ui/firewall/README.md) for more details. The UI only displays the packets and does not store or analyze anything. You can develop your own backend to listen to the event stream, store the data in your preferred format, perform analysis, and create a custom UI to display information that will help you improve the firewall and enhance the protection of your machine.

Our investigation lead to the final decision

- Linux: iptables
- Macos: Not implemented
- Windows: Not implemented

## Linux

To be a firewall, the miner will have to be able to

- listen incoming packets.
- manage rules to allow/deny packets.

To manage rules, we are going to use **iptables**

To listen incoming packets, we can not use Scapy because, by default, it captures packets as they pass through the network interface, but this does not prevent the packets from being processed by the miner simultaneously via fast api. This means that both Scapy and the application can receive the packet almost concurrently, which might lead to the observed behavior where the application processes the packet before the firewall can drop it.

To solve that issue, we decided to configure some rules in iptables using queue and then use **NetfilterQueue** which is a Python library that provides access to packets that have been matched by iptables rules and placed into a user-space queue. It allows you to process packets in user space rather than in the kernel, enabling advanced packet manipulation, inspection, and decision-making before the packets are accepted, dropped, or otherwise handled.

By using **iptables** and **NetfilterQueue**, we guarantee any packets will go through the miner firewall before going to the miner itself which avoid any unexpected requests to be proceed by the miner.

## Macos

Firewall is not implemented for Macos.

## Windows

Firewall is not implemented for Window.

<br />

# Installation

> IMPORTANT <br />
> Modifying iptables rules can block access to your machine, potentially leaving you with no choice but to reinstall your VPS.
> Please be careful when managing iptables. We recommend using our scripts on a testnet VPS first.

> IMPORTANT <br />
> Please ensure your SSH port is set to 22, as this is the port we will allow. If you do not restore the default setting before starting the installation, you may lose access to your machine.

Before installing the firewall using one of the two possible methods, some packages need to be installed as prerequisites.

```bash
./scripts/os/os_setup.sh -t miner
```

## Manual Installation

To install the firewall, add the argument `--firewall.on` to the start command.

```bash
pm2 start neurons/miner.py \
  --name MINER_NAME \
  --interpreter python3 -- \
  --netuid 7 \
  --subtensor.network local \
  --wallet.name miner \
  --wallet.hotkey miner-7 \
  --logging.debug \
  --auto-update \
  --firewall.on
```

Options

- `--firewall.interface` - Network interface to listen for traffic on, default is `eth0`.
- `--firewall.config` - Path to the firewall configuration file, default is `firewall.json`.
- `--sse.firewall.ip` - IP address of the firewall UI consumer to allow traffic only from that source.

## Automatic Installation

To install the firewall, run the following script

```bash
python3 scripts/firewall/firewall_activate.py --process.name MINER_NAME
```

Options

- `--process.name` - Name of the miner used by pm2.
- `--firewall.interface` - Network interface to listen for traffic on, default is `eth0`.
- `--firewall.config` - Path to the firewall configuration file, default is `firewall.json`.

Replace `MINER_NAME` by the name of your miner.

Check the process arguments

```bash
pm2 show MINER_NAME
```

You should see something like

```bash
script args       │ --netuid 7 --subtensor.network local --wallet.name miner --wallet.hotkey default --logging.debug --firewall.on
```

> IMPORTANT: Be sure you do **HAVE** the argument `--firewall.on`

Check the miner log

```bash
pm2 log MINER_NAME
```

You should see some firewall logs such as

```bash
12|miner-60  | 2024-06-24 19:02:32.133 |      DEBUG       |  - Starting firewall on interface eth0 -
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

<br />

# Uninstallation

> IMPORTANT <br />
> Modifying iptables rules can block access to your machine, potentially leaving you with no choice but to reinstall your VPS.
> Please be careful when managing iptables. We recommend using our scripts on a testnet VPS first.

## Manual Uninstallation

To uninstall the firewall, remove the argument `--firewall.on` to the start command.

```bash
pm2 start neurons/miner.py \
  --name MINER_NAME \
  --interpreter python3 -- \
  --netuid 7 \
  --subtensor.network local \
  --wallet.name miner \
  --wallet.hotkey miner-7 \
  --logging.debug \
  --auto-update
```

## Automatic Uninstallation

To uninstall the firewall, run the following script

```bash
python3 scripts/firewall/firewall_deactivate.py --process.name MINER_NAME
```

Options

- `--process.name` - Name of the miner used by pm2.
- `--firewall.interface` - Network interface to listen for traffic on, default is `eth0`.
- `--firewall.config` - Path to the firewall configuration file, default is `firewall.json`.

Replace `MINER_NAME` by the name of your miner.

Check the process arguments

```bash
pm2 show MINER_NAME
```

You should see something like

```bash
script args       │ --netuid 7 --subtensor.network local --wallet.name miner --wallet.hotkey default --logging.debug
```

> IMPORTANT: Be sure you do **NOT HAVE** the argument `--firewall.on`

Check the miner log

```bash
pm2 log MINER_NAME
```

You should not see any firewall logs, so you should not see the following

```bash
12|miner-60  | 2024-06-24 19:02:32.133 |      DEBUG       |  - Starting firewall on interface eth0 -
```

Check the iptables

```bash
sudo iptables -n -v -L INPUT
```

You should not see any rules mentioning in the activation of the firewall, so you should see something

```bash
Chain INPUT (policy ACCEPT 15481 packets, 1415K bytes)
 pkts bytes target     prot opt in     out     source               destination
```

<br />

# Rules

Explain the type of rules (static, dynamic and custom rules)

Until futher investigation, SubVortex team has decided

- **Subtensor** - no rules applied, everything coming from ports 9933, 9944 and 30333 will be allowed.
- **Miner** - all dynamic rules are applied for the miner. See [Dynamic rules](#dynamic-rules) for more details.

## Static rules

The static rules are rules that do not change once created without futher analysis.

The static rules proposed for SubVortex are:

- **Default DROP Policy for the INPUT Chain** - By default, all incoming traffic that does not mactch a rule will be denied.
- **ACCEPT all traffic on the loopback interface (lo)** - The rule allows all incoming traffic on the loopback interface, which is used for internal communication within the same machine. Use case: Ensures that local applications can communicate with each other.
- **ACCEPT incoming SSH traffic on port 22** - The rule allows incoming TCP traffic on port 22, which is typically used for SSH connections. Use case: Allows remote administrative access to the server via SSH.
- **ACCEPT incoming HTTPS traffic on port 443** - The rule allows incoming TCP traffic on port 443, which is used for secure HTTPS connections. Use case: Enables secure web traffic to be served by the server for websites and APIs.
- **ACCEPT outgoing HTTPS traffic from port 443** - The rule allows outgoing TCP traffic from port 443, ensuring that responses to HTTPS requests can be sent out. Use case: Ensures that the server can send back responses to HTTPS requests it received.
- **ACCEPT outgoing HTTP traffic from port 80** - The rule allows outgoing TCP traffic from port 80, ensuring that responses to HTTP requests can be sent out. Use case: Ensures that the server can send back responses to HTTP requests it received.
- **ACCEPT outgoing DNS traffic from port 53** - The rule allows outgoing UDP traffic from port 53, which is used for DNS queries. Use case: Enables the server to perform DNS lookups, essential for resolving domain names to IP addresses.
- **ACCEPT incoming TCP traffic on port 9944** - The rule allows all incoming traffic on port 9944 to be placed into a user-space queue that will for now accept all traffic.
- **ACCEPT incoming TCP traffic on port 9933** - The rule allows all incoming traffic on port 9933 to be placed into a user-space queue that will for now accept all traffic.
- **ACCEPT incoming TCP traffic on port 30333** - The rule allows all incoming traffic on port 30333to be placed into a user-space queue that will for now accept all traffic.
- **ACCEPT incoming TCP traffic on port source 30333** - The rule allows all incoming traffic coming from source port 30333. Use case: Ensures bidirectional communication which may be necessary if stateful connection tracking is not in place or functioning correctly
- **Queue incoming TCP traffic on port 8091 to user space for processing** - The rule allow all incoming traffic on port 8091 to be placed into a user-space queue to be allowed/dropped by the miner firewall after analysing ay potential attacks.

For the subtensor ports, we decided for now to accept all traffic as we need more time to investigate what will be the best configuration to detect any DoS/DDoS attacks.

## Dynamic rules

The dynamic rules are rules analysing what is happening in the subnet/network to take a final decision on allowing/denying the traffic.

The dynamic rules proposed for SubVortex are

- **Hotkey Blacklisted** - The rule denies all incoming traffic coming from a validator with not enough stake.
- **Wrong Synapse** - The rule denies all incoming traffic using an inexistant synapse.
- **Old Validator Version** - The rule denies all incoming traffic coming from a validator with an old neuron version.
- **Wrong Signature** - The rule denies all incoming traffic containing an expected signature.
- **Denial of Service (DoS)** - The rule denies all incoming traffic that has been flagged as DoS.
- **Distributed Denial of Service (DDoS)** - The rule denies all incoming traffic that has been flagged as DDoS.

### Hotkey Blacklisted Rule

The rule denies all incoming traffic coming from a validator with not enough stake.

The rule uses, in real time, the hotkeys of all valid validators and deny any traffic coming from any hotkey that is not part of that list.

The rule is not configurable and so can not be changed without changing the source code which is not recommended.

### Wrong Synapse Rule

The rule denies all incoming traffic using an inexistant synapse.

The rule uses the synapse attached when starting the axon and deny any traffic sending a synapse that does not exist.

The rule is not configurable and so can not be changed without changing the source code which is not recommended.

### Old Validator Version Rule

The rule denies all incoming traffic coming from a validator with an old neuron version.

The rule uses the version set in the hyperparameter `weights_version` and deny any traffic sending a neuron version oldest than that one.

The rule is not configurable and so can not be changed without changing the source code which is not recommended.

### Denial of Service Rule

The rule denies all incoming traffic that has been flagged as DoS.

The rule involves multiple compromised devices (often part of a botnet) sending a massive number of requests to the target server simultaneously. The distributed nature of the attack makes it more difficult to mitigate because it originates from many different sources.

A DoS rule allow to detect attacks on traffic coming from a unique ip and going to a specific port.

The structure of the rule is as follows:

- **dport** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `detect-dos`
- **configuration** - Configuration used to detect if the traffic has to be blocked or not
- **configuration.time_window** - Time duration over which incoming traffic is monitored (time in seconds).
- **configuration.packet_threshold** - Maximum number of packets allowed within the specified time_window before considering it a potential attack.

> IMPORTANT <br />
> The structure has to provide an ip or a port.

For example,

```json
{
  "dport": 8091,
  "protocol": "tcp",
  "type": "detect-dos",
  "configuration": {
    "time_window": 300,
    "packet_threshold": 4
  }
}
```

The protocol can be only TCP.

No IP property will be provided as we want to listen to traffic coming from all IP addresses.

The settings above are the ones we encourage using. The validator selects 10 miners per step and needs a maximum of 5 minutes to go through all of them. So, potentially, if your UID is selected, you will receive 2 requests (Synapse and Score) within the 5 minutes (300 seconds). So, we allow 2 requests coming for a specific IP every 300 seconds.

You are free to adjust the configuration as needed based on your research but at your own risks. Feel free to communicate with the community to find the settings that best suit the subnet.

The rule counts the number of requests received within a specified time window for each combination of IP address, port, and protocol. If the total number of requests exceeds the current requests will be blocked.

### Distributed Denial of Service Rule

The rule denies all incoming traffic that has been flagged as DDoS.

The rule aims to make a machine or network resource unavailable to its intended users by overwhelming the system with a flood of illegitimate requests, thereby exhausting the server's resources (CPU, memory, bandwidth) and causing it to slow down or crash.

A DDoS rule allow to detect attacks on traffic coming from multiple ips and going to a specific port.

The structure of the rule is as follows:

- **dport** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `detect-dos`
- **configuration** - Configuration used to detect if the traffic has to be blocked or not
- **configuration.time_window** - Time duration over which incoming traffic is monitored (time in seconds).
- **configuration.packet_threshold** - Maximum number of packets allowed within the specified time_window before considering it a potential attack.

> IMPORTANT <br />
> The structure has to provide an ip or a port.

For example,

```json
{
  "dport": 8091,
  "protocol": "tcp",
  "type": "detect-ddos",
  "configuration": {
    "time_window": 300,
    "packet_threshold": 128
  }
}
```

The protocol can be only TCP.

No IP property will be provided as we want to listen to traffic coming from all IP addresses.

The settings above are the ones we encourage using. The validator selects 10 miners per step and needs a maximum of 5 minutes to go through all of them. So, potentially, if your UID is selected, you will receive two requests (Synapse and Score) within the 5 minutes. Besides, we can have a maximum of 64 validators which can all select the same miner (it is probably not possible anymore but until we can bring certitude on a more narrow configuration we are going to play safe here). So, we allow 128 (64 \* 2) requests coming for different IPs every 300 seconds.

You are free to adjust the configuration as needed based on your research but at your own risks. Feel free to communicate with the community to find the settings that best suit the subnet.

The rule cannot simply count the number of requests across all VPS and compare it to a benchmark, as we do for DoS attacks, because some legitimate VPS may be flagged unfairly. For example, if a malicious VPS sends the right number of requests and a legitimate VPS sends the last request that triggers the alert, the legitimate VPS will be flagged as a DDoS attacker, which is incorrect.

So, here the solution we implemented for SubVortex
![DDoS Explanation](../assets/firewall-ddos.png)

The rule visually distinguishes between legitimate user activity and potential DDoS attacks by analyzing request patterns from various VPS (IP) addresses. Each blue dot represents the number of requests from a specific VPS. The orange line represents the 75th percentile, dividing the VPS into two categories: the legit group (below the 75th percentile) and the potential attackers group (above the 75th percentile). The green line indicates the mean number of requests within the legit group, serving as a baseline for normal activity and helping to follow the trend more effectively than using only the percentile or another static value. The benchmark line (red) is established by adding the legit group's mean to the maximum number of requests within the same group. Any VPS exceeding this benchmark is flagged as a potential DDoS attacker. This approach ensures accurate identification of abnormal request patterns while minimizing false positives.

## Custom rules

The custom rules are rules that are defined by the user. For SubVortex, no custom rules are needed.

However, some other rules can be used at your own risks

- **Allow Rule** - The rule allows incoming traffic from specified IP addresses and/or ports.
- **Deny Rule** - The rule denies incoming traffic from specified IP addresses and/or ports.

### Allow rule

The rule allows incoming traffic from specified IP addresses and/or ports.

The structure of the rule is as follows:

- **ip** - IP source to allow traffic from
- **port** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `allow`

> IMPORTANT <br />
> The structure has to provide an ip and/or a port.

#### Allow rule on IP

To create an allow rule on ip

```json
{
  "ip": "192.168.10.1",
  "protocol": "tcp",
  "type": "allow"
}
```

This rule allows all traffic from the ip `192.168.10.1`.

#### Allow rule on Port

To create an allow rule on port

```json
{
  "port": 9933,
  "protocol": "tcp",
  "type": "allow"
}
```

The protocol can be only TCP.

This rule allows all traffic to port 9933.

#### Allow rule on IP/Port

To create ann allow rule on ip/port

```json
{
  "ip": "192.168.10.1",
  "port": 9933,
  "protocol": "tcp",
  "type": "allow"
}
```

This rule allows all traffic from the ip `192.168.10.1` to a the port 9933.

### Deny rule

The rule denies incoming traffic from specified IP addresses and/or ports.

The structure of the rule is as follows:

- **ip** - IP source to allow traffic from
- **port** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `deny`

> IMPORTANT <br />
> The structure has to provide an ip and/or a port.

#### Deny rule on IP

To create an deny rule on ip

```json
{
  "ip": "192.168.10.1",
  "protocol": "tcp",
  "type": "deny"
}
```

This rule dnies all traffic from the ip `192.168.10.1`.

#### Deny rule on Port

To create an deny rule on port

```json
{
  "port": 9933,
  "protocol": "tcp",
  "type": "deny"
}
```

The protocol can be only TCP.

This rule dnies all traffic to a the port 9933.

#### Deny rule on IP/Port

To create ann deny rule on ip/port

```json
{
  "ip": "192.168.10.1",
  "port": 9933,
  "protocol": "tcp",
  "type": "deny"
}
```

This rule dnies all traffic from the ip `192.168.10.1` to a the port 9933.

<br />

# Contributions

We are open to contributions from everyone who is interested in improving this firewall. While we welcome all types of contributions, we especially need help with features and enhancements that are still pending, as outlined in this documentation. If you're interested in contributing, please contact the team. Your support and collaboration are highly valued as we work together to enhance this project. Thank you for considering contributing!

<br />

# UI

To install the UI, please refer to the [UI Guide](../../ui/firewall/README.md)

<br />

# Recommendations

It is highly recommended to enable the firewall to protect your miner and use the default configuration provided. You are free to adjust the configuration file as you wish, but at your own risks. Please share with the community if you find good settings.

> IMPORTANT <br />
> The order of rules in iptables is critical because the first matching rule is the one that gets applied. Careful planning and management of rule order can ensure the firewall behaves as intended.
