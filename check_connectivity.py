#/usr/bin/env python3
import csv
from netmiko import ConnectHandler

#csv files for connectivity and mac of R2 and R3
ROUTERS_INFO_CSV = "routers_info.csv"
MAC_CSV = "mac_addresses.csv"

#load r4 and r5 information from CSV
def load_router_info(file_path):
    """Loads router credentials and interfaces from a single CSV file."""
    router_info = {}
    with open(file_path, mode="r", encoding="utf8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ipv6 = row["host"]
            router_info[ipv6] = {
                "device_type": row["device_type"],
                "host": row["host"],
                "username": row["username"],
                "password": row["password"],
                "router": row["Router"],
                "interface": row["Interface"]
            }
    return router_info

# Load MAC addresses from CSV
def load_mac_addresses():
    """Loads MAC addresses for DHCP from CSV"""
    mac_addresses = {}
    with open(MAC_CSV, newline='', encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mac_addresses[row["Router"]] = row["MAC Address"]
    return mac_addresses

def test_ssh_connection(credentials):
    """Tests SSH connection to a router."""
    try:
        net_connect = ConnectHandler(**credentials)
        net_connect.disconnect()
        return True
    except Exception as e:
        print(f"SSH connection failed for {credentials['host']}: {str(e)}")
        return False

def get_r5_ipv6_address(r4_creds, r5_creds):
    """Retrieve R5's Global Unicast IPv6 address using R4's neighbor table."""
    try:
        # Step 1: Get R5's MAC address from R4
        net_connect = ConnectHandler(**r4_creds)
        output = net_connect.send_command("show ipv6 neighbors")
        net_connect.disconnect()
    except Exception as e:
        print(f"Failed to retrieve R5 MAC address from R4: {str(e)}")
        return None

    r5_mac = None
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) > 2 and "C805:17FF:FE5F:0" in parts[0]:  # Match R5 link-local address
            r5_mac = parts[1].replace(".", "").lower()  # Normalize MAC format
            break

    if not r5_mac:
        print("Error: Could not determine R5 MAC address from R4.")
        return None

    print(f"Detected R5 MAC Address: {r5_mac}")

    try:
        # Step 2: Find matching IPv6 address on R5
        net_connect = ConnectHandler(**r5_creds)
        output = net_connect.send_command("show ipv6 interface brief")
        net_connect.disconnect()
    except Exception as e:
        print(f"Failed to retrieve IPv6 address from R5: {str(e)}")
        return None

    for line in output.split("\n"):
        parts = line.split()
        if len(parts) > 1 and "2001:1111:2222:3333" in parts[0]:  # Check Global Unicast
            return parts[0]  # Return R5's IPv6 address

    print("Error: Could not find R5's global IPv6 address.")
    return None

if __name__ == "__main__":
    print("Loading router and MAC address data...")
    router_info = load_router_info(ROUTERS_INFO_CSV)
    mac_addresses = load_mac_addresses()

    print("\nChecking if all required data is available...")
    if not router_info:
        print("Error: No router data found in routers_info.csv")
        exit()
    if not mac_addresses:
        print("Error: No MAC address data found in mac_addresses.csv")
        exit()

    print("\nLoaded router information:")
    for ipv6, data in router_info.items():
        print(f"Router: {data['router']}, IPv6: {ipv6}, Interface: {data['interface']}")

    print("\nLoaded MAC addresses:")
    for router, mac in mac_addresses.items():
        print(f"Router: {router}, MAC: {mac}")

    print("\nFinding R4 IPv6 address for Tap0...")
    r4_ipv6 = None
    for ipv6, data in router_info.items():
        if data["router"] == "R4" and data["interface"] == "Tap0":
            r4_ipv6 = ipv6
            break

    if not r4_ipv6:
        print("Error: Could not determine R4 IPv6 address for Tap0.")
        exit()

    print(f"R4 IPv6 Address for Tap0: {r4_ipv6}")

    print("\nTesting SSH connection to R4...")
    r4_creds = router_info.get(r4_ipv6)
    if not r4_creds:
        print(f"Error: No credentials found for R4 ({r4_ipv6}).")
        exit()

    if not test_ssh_connection(r4_creds):
        print("Error: Unable to connect to R4 via SSH.")
        exit()

    print("Successfully connected to R4.")

    print("\nFinding R5 IPv6 address from R4's neighbor table...")
    r5_ipv6 = get_r5_ipv6_address(r4_creds, router_info)
    if not r5_ipv6:
        print("Error: Could not retrieve R5 IPv6 address from R4.")
        exit()

    print(f"R5 IPv6 Address: {r5_ipv6}")

    print("\nTesting SSH connection to R5...")
    r5_creds = router_info.get(r5_ipv6)
    if not r5_creds:
        print(f"Error: No credentials found for R5 ({r5_ipv6}).")
        exit()

    if not test_ssh_connection(r5_creds):
        print("Error: Unable to connect to R5 via SSH.")
        exit()

    print("Successfully connected to R5.")

    print("\nAll data and connections verified successfully.")
