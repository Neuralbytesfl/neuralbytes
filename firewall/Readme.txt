# Real-Time SYN Connection Monitor and Subnet Blocker

This Python script monitors active network connections in real-time, identifies suspicious activity based on configurable thresholds, and blocks offending subnets dynamically using `iptables`. It is designed to help mitigate network abuse, such as botnets or denial-of-service attacks, by automatically detecting and responding to excessive or persistent connection activity.

---

## **Features**

- **Real-Time Monitoring**: Continuously monitors active TCP connections in the `ESTABLISHED` state.
- **Dynamic Blocking**: Automatically blocks subnets exceeding predefined thresholds using `iptables`.
- **Aggressive Cleanup**: Terminates existing connections from blocked subnets using `conntrack`.
- **Sliding Window History**: Tracks connection counts over a configurable time window for more accurate detection of slow or persistent attacks.
- **Configurable Parameters**: Easily adjust thresholds, monitoring intervals, and history windows.

---

## **How It Works**

1. **Monitoring Connections**:
   - The script uses `netstat` to retrieve active TCP connections.
   - Subnets are extracted from source IPs and grouped into `/24` blocks.

2. **Threshold Detection**:
   - Subnets exceeding a **connection threshold** in a single interval are immediately blocked.
   - Persistent activity over multiple intervals is also flagged and blocked.

3. **Blocking Subnets**:
   - Adds a rule to `iptables` to drop all traffic from the offending subnet.
   - Uses `conntrack` to terminate any existing connections from the subnet.

4. **Real-Time Updates**:
   - Displays active connections and blocked subnets in the terminal.

---

## **Configuration Parameters**

You can adjust the following parameters to customize the script's behavior:

- `THRESHOLD`: Maximum simultaneous connections allowed per subnet before immediate blocking (default: 10).
- `HISTORY_WINDOW`: Number of intervals to track for persistent activity (default: 5).
- `INTERVAL`: Monitoring interval in seconds (default: 1 second).
- `PERSISTENT_THRESHOLD`: Total connections over the history window to trigger blocking (default: 25).

---

## **Requirements**

1. **Python 3.x**: Ensure Python 3 is installed on your system.
2. **Required Tools**:
   - `iptables`: To manage network traffic rules.
   - `conntrack`: For aggressively terminating active connections.
3. **Linux Environment**: This script is designed to work on Linux-based systems.

To install `conntrack`, run:
```bash
sudo apt install conntrack
