[Back to Main README](../../README.md)

Miners can be subjected to various attacks daily, such as DoS (Denial of Service) and DDoS (Distributed Denial of Service).

To protect miners, owners can enable the firewall feature available on all miners.

<br />

---

- [Prerequisites](#prerequisites)
- [Installation](#intasllation)
- [Uninstallation](#uninstallation)
- [Configuration](#configuration)
- [Recommendations](#recommendations)

---

<br />

# Prerequisites

Use the firewall if you are not on macOS or Windows, or on any VPS that does not have `iptables` available. You can check if this command-line interface (CLI) exists by running:

```bash
type iptables
```

You should see something as

```bash
iptables is hashed (/usr/sbin/iptables)
```

In the future, we will try to add support for other firewall CLIs to cover macOS, Windows, and any other types of operating systems.

# Installation

To enable the firewall on the miner, add the argument `--firewall.on` to the start command.

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

<br />

# Uninstallation

To disable the firewall on the miner, remove the argument `--firewall.on` to the start command.

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

# Configuration

By default, any traffic that does not match any rules will be blocked. A default configuration file with basic rules is provided, see [firewall.json](../../firewall.json).

A custom configuration file can be provided to add specific rules to the firewall. The possible rules are:

- **Allow rule**: Allows traffic coming from an IP and/or going to a port.
- **Deny rule**: Denies traffic coming from an IP and/or going to a port.
- **Detect rule**: Detects certain attacks on traffic coming from an IP and/or going to a port.

## Allow rule

An allow rule permits traffic from specified IP addresses and/or ports.

The structure of the rule is as follows:

- **ip** - IP source to allow traffic from
- **port** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `allow`

> IMPORTANT <br />
> The structure as to provide an ip or a port.

### Allow rule on IP

To create an allow rule on ip

```json
{
  "ip": "192.168.10.1",
  "protocol": "tcp",
  "type": "allow"
}
```

This rule allows all traffic from the ip `192.168.10.1`.

### Allow rule on Port

To create an allow rule on port

```json
{
  "port": 9933,
  "protocol": "tcp",
  "type": "allow"
}
```

The protocol can be any existing protocol, but it is most commonly TCP.

This rule allows all traffic to port 9933.

### Allow rule on IP/Port

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

## Deny rule

An deny rule permits traffic from specified IP addresses or ports.

The structure of the rule is as follows:

- **ip** - IP source to allow traffic from
- **port** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `deny`

> IMPORTANT <br />
> The structure as to provide an ip or a port.

### Deny rule on IP

To create an deny rule on ip

```json
{
  "ip": "192.168.10.1",
  "protocol": "tcp",
  "type": "deny"
}
```

This rule dnies all traffic from the ip `192.168.10.1`.

### Deny rule on Port

To create an deny rule on port

```json
{
  "port": 9933,
  "protocol": "tcp",
  "type": "deny"
}
```

The protocol can be any existing protocol but will by most of the time TCP.

This rule dnies all traffic to a the port 9933.

### Deny rule on IP/Port

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

## Detect rule

An detect rule permits to detect some potential attacks on traffic from specified IP addresses or ports. The current attacks detected are

- DoS (Denial of Service) - it involves multiple compromised devices (often part of a botnet) sending a massive number of requests to the target server simultaneously. The distributed nature of the attack makes it more difficult to mitigate because it originates from many different sources.
- DDoS (Distributed Denial of Service) - it aims to make a machine or network resource unavailable to its intended users by overwhelming the system with a flood of illegitimate requests, thereby exhausting the server's resources (CPU, memory, bandwidth) and causing it to slow down or crash.

### DoS rule

A DoS rule allow to detect attacks on traffic coming from a unique ip and going to a specific port.

The structure of the rule is as follows:

- **port** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `detect-dos`
- **configuration** - Configuration used to detect if the traffic has to be blocked or not
- **configuration.time_window** - Time duration over which incoming traffic is monitored (time in seconds).
- **configuration.packet_threshold** - Maximum number of packets allowed within the specified time_window before considering it a potential attack.

> IMPORTANT <br />
> The structure as to provide an ip or a port.

For example,

```json
{
  "port": 8091,
  "protocol": "tcp",
  "type": "detect-dos",
  "configuration": {
      "time_window": 300,
      "packet_threshold": 1
  }
}
```

The protocol can be any existing protocol, but it is most commonly TCP.

No IP property will be provided as we want to listen to traffic coming from all IP addresses.

The settings above are the ones we encourage using. The validator selects 10 miners per step and needs a maximum of 5 minutes to go through all of them. So, potentially, if your UID is selected, you will receive one request within the 5 minutes (300 seconds). So, we allow 1 request coming for a specific IP every 300 seconds.

You are free to adjust the configuration as needed based on your research. Feel free to communicate with the community to find the settings that best suit your needs.

### DDoS rule

A DDoS rule allow to detect attacks on traffic coming from multiple ips and going to a specific port.

The structure of the rule is as follows:

- **port** - Port destination to allow traffic to
- **protocol** - Protocol destination to allow traffic to
- **type** - type of the rule, which is `detect-dos`
- **configuration** - Configuration used to detect if the traffic has to be blocked or not
- **configuration.time_window** - Time duration over which incoming traffic is monitored (time in seconds).
- **configuration.packet_threshold** - Maximum number of packets allowed within the specified time_window before considering it a potential attack.

> IMPORTANT <br />
> The structure as to provide an ip or a port.

For example,

```json
{
  "port": 8091,
  "protocol": "tcp",
  "type": "detect-ddos",
  "configuration": {
      "time_window": 300,
      "packet_threshold": 30
  }
}
```

The protocol can be any existing protocol, but it is most commonly TCP.

No IP property will be provided as we want to listen to traffic coming from all IP addresses.

The settings above are the ones we encourage using. The validator selects 10 miners per step and needs a maximum of 5 minutes to go through all of them. So, potentially, if your UID is selected, you will receive one request within the 5 minutes. Besides, there are currently 20 validators but we take an extra 10 just in case. So, we allow 30 requests coming for different IPs every 300 seconds.

You are free to adjust the configuration as needed based on your research. Feel free to communicate with the community to find the settings that best suit your needs.

## Default config file

Here's the revised version:

By default, a configuration file is provided with the following settings:

- Blocking all IPs and ports by default
- Detecting DoS attacks on miner port 8091
- Detecting DDoS attacks on miner port 8091
- Allowing traffic on FTP port 22
- Allowing traffic on Subtensor ports 9944, 9933, and 30333

You are free to add more allow and deny rules as you wish, but at your own risk.

> IMPORTANT: <br />
> Do not hesitate to share any detect rules you would like us to add to the firewall.

For more details, see the file `firewall.json`

<br />

# Recommendations

It is highly recommended to enable the firewall to protect your miner and use the default configuration provided. You are free to adjust the configuration file as you wish, but at your own risk.

> IMPORTANT <br />
> The order of rules in iptables is critical because the first matching rule is the one that gets applied. Careful planning and management of rule order can ensure the firewall behaves as intended.
