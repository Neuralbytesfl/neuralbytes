import os
import subprocess
import time
from collections import defaultdict, deque

# Parameters
THRESHOLD = 10  # Connections per subnet to trigger immediate block
HISTORY_WINDOW = 5  # Number of intervals to track
INTERVAL = 1  # Monitoring interval in seconds
PERSISTENT_THRESHOLD = 25  # Total connections over the history window to block

# Connection history: {subnet: deque([counts_per_interval])}
connection_history = defaultdict(lambda: deque(maxlen=HISTORY_WINDOW))
blocked_subnets = set()


def get_active_connections():
    """
    Use netstat to retrieve active connections in ESTABLISHED state.
    Returns a dictionary of subnets and connection counts.
    """
    result = subprocess.run(
        ["netstat", "-nt"],
        stdout=subprocess.PIPE,
        text=True
    )
    lines = result.stdout.splitlines()

    connections = defaultdict(int)
    for line in lines:
        if "ESTABLISHED" in line:  # Only count established connections
            parts = line.split()
            if len(parts) >= 5:
                source_ip = parts[4].split(":")[0]
                # Extract /24 subnet (first 3 octets)
                subnet = ".".join(source_ip.split(".")[:3]) + ".0/24"
                connections[subnet] += 1

    return connections


def block_subnet(subnet):
    """
    Add an iptables rule to drop all traffic from the offending subnet
    and terminate existing connections.
    """
    if subnet not in blocked_subnets:
        print(f"\033[91mBlocking subnet: {subnet}\033[0m")  # Red text for blocked subnets
        os.system(f"iptables -A INPUT -s {subnet} -j DROP")
        os.system("iptables-save > /etc/iptables/rules.v4")

        # Terminate existing connections aggressively
        print(f"Terminating active connections for subnet: {subnet}")
        os.system(f"conntrack -D -s {subnet}")
        blocked_subnets.add(subnet)


def monitor_connections():
    """
    Monitor active connections and block subnets exceeding thresholds.
    """
    global connection_history, blocked_subnets

    while True:
        active_connections = get_active_connections()
        print("\033[2J\033[H")  # Clear the terminal
        print("Active Connections:")
        print("--------------------")

        for subnet, count in active_connections.items():
            print(f"{subnet}: {count} connections")

            # Update connection history
            connection_history[subnet].append(count)

            # Immediate block for high connection rates
            if count > THRESHOLD:
                block_subnet(subnet)

            # Check persistent activity over history window
            if subnet not in blocked_subnets:
                total_connections = sum(connection_history[subnet])
                if total_connections > PERSISTENT_THRESHOLD:
                    print(f"\033[93mPersistent activity detected: {subnet} ({total_connections} connections)\033[0m")
                    block_subnet(subnet)

        print("\nBlocked Subnets:")
        print("--------------------")
        for subnet in blocked_subnets:
            print(f"{subnet} (Blocked)")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    print("Starting SYN connection monitor...")
    try:
        # Ensure conntrack is installed
        if os.system("which conntrack > /dev/null") != 0:
            print("\033[91mError: conntrack is not installed. Install it with 'sudo apt install conntrack'.\033[0m")
            exit(1)
        monitor_connections()
    except KeyboardInterrupt:
        print("\nExiting...")
