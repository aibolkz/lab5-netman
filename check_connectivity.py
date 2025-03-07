#/usr/bin/env python3
import csv
import json
from netmiko import ConnectHandler

# csv and json file paths
ROUTERS_INFO_CSV = "routers_info.csv"
MAC_JSON = "mac_addr.json"

# load router credentials from csv
def load_router_info(file_path):
    router_info = {}
    with open(file_path, mode="r", encoding="utf8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ipv6 = row["host"]
            router_info[ipv6] = {
                "device_type": row["device_type"],
                "host": row["host"],
                "username": row["username"],
                "password": row["password"]
            }
    return router_info

# load mac addresses from json
def load_mac_addresses():
    try:
        with open(MAC_JSON, "r", encoding="utf8") as jsonfile:
            mac_addresses = json.load(jsonfile)
            if not isinstance(mac_addresses, list):
                raise ValueError("invalid json format: expected a list of mac addresses.")
            return mac_addresses
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"error loading mac addresses from {MAC_JSON}: {str(e)}")
        return []

# test ssh connection to a router
def test_ssh_connection(credentials):
    try:
        net_connect = ConnectHandler(**credentials)
        net_connect.disconnect()
        return True
    except Exception as e:
        print(f"ssh connection failed for {credentials['host']}: {str(e)}")
        return False

# get r5 global ipv6 address using r4's neighbor table
def get_r5_ipv6_address(r4_creds, r5_host):
    try:
        net_connect = ConnectHandler(**r4_creds)
        output = net_connect.send_command("show ipv6 neighbors")
        net_connect.disconnect()
    except Exception as e:
        print(f"failed to retrieve r5 mac address from r4: {str(e)}")
        return None

    r5_mac = None
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) > 2 and r5_host in parts[0]:  # match r5 ipv6 address in neighbor table
            r5_mac = parts[1].replace(".", "").lower()
            break

    if not r5_mac:
        print("error: could not determine r5 mac address from r4.")
        return None

    print(f"detected r5 mac address: {r5_mac}")

    return r5_host  # return r5 ipv6 address from csv

if __name__ == "__main__":
    print("loading router and mac address data...")
    router_info = load_router_info(ROUTERS_INFO_CSV)
    mac_addresses = load_mac_addresses()

    print("\nchecking if all required data is available...")
    if not router_info:
        print("error: no router data found in routers_info.csv")
        exit()
    if not mac_addresses:
        print(f"error: no mac address data found in {MAC_JSON}")
        exit()

    print("\nloaded router information:")
    for ipv6, data in router_info.items():
        print(f"host: {data['host']}, ipv6: {ipv6}")

    print("\nloaded mac addresses:")
    for mac in mac_addresses:
        print(f"mac address: {mac}")

    # get first R4 found in csv
    r4_host = next((ipv6 for ipv6 in router_info if "db8:1::2" in ipv6), None)
    if not r4_host:
        print("error: could not determine r4 ipv6 address.")
        exit()
    r4_creds = router_info[r4_host]

    print(f"\nr4 ipv6 address: {r4_host}")

    print("\ntesting ssh connection to r4...")
    if not test_ssh_connection(r4_creds):
        print("error: unable to connect to r4 via ssh.")
        exit()
    print("successfully connected to r4.")

    # get first R5 found in csv
    r5_host = next((ipv6 for ipv6 in router_info if "C805:17FF:FE5F:0" in ipv6), None)
    if not r5_host:
        print("error: could not determine r5 ipv6 address.")
        exit()
    print(f"\nr5 ipv6 address: {r5_host}")

    # get r5 ipv6 address from r4 neighbor table
    r5_ipv6 = get_r5_ipv6_address(r4_creds, r5_host)
    if not r5_ipv6:
        print("error: could not retrieve r5 ipv6 address from r4.")
        exit()

    # get r5 credentials
    r5_creds = router_info.get(r5_ipv6)
    if not r5_creds:
        print(f"error: no credentials found for r5 ({r5_ipv6}).")
        exit()

    print("\ntesting ssh connection to r5...")
    if not test_ssh_connection(r5_creds):
        print("error: unable to connect to r5 via ssh.")
        exit()
    print("successfully connected to r5.")

    print("\nall data and connections verified successfully.")
