#/usr/bin/env python3
import csv
import json
from netmiko import ConnectHandler
import time

#csv and json file paths
ROUTERS_INFO_CSV = "routers_info.csv"
MAC_JSON = "mac_addr.json"

#load router credentials from csv
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

#load mac addresses from json
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

#test ssh connection to a router
def test_ssh_connection(credentials):
    try:
        net_connect = ConnectHandler(**credentials)
        net_connect.disconnect()
        return True
    except Exception as e:
        print(f"ssh connection failed for {credentials['host']}: {str(e)}")
        return False

#get r5 global ipv6 address using r4's neighbor table
def get_r5_ipv6_address(r4_creds):
    try:
        net_connect = ConnectHandler(**r4_creds)
        output = net_connect.send_command("show ipv6 neighbors")
        net_connect.disconnect()
    except Exception as e:
        print(f"failed to retrieve r5 ipv6 address from r4: {str(e)}")
        return None

    r5_ipv6 = None
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) > 1 and parts[0].startswith("2001:1111:2222:3333"):  # match global IPv6
            r5_ipv6 = parts[0]
            break  # Stop at the first valid global IPv6

    if not r5_ipv6:
        print("error: could not determine r5 global ipv6 address from r4.")
        return None

    print(f"detected r5 global ipv6 address: {r5_ipv6}")
    return r5_ipv6

#configure dhcp server on r5
def configure_dhcp_on_r5(r5_creds, mac_addresses):
    try:
        net_connect = ConnectHandler(**r5_creds)

        dhcp_config = [
            "int fa0/0", 
            "ip address 192.168.20.1 255.255.255.0",
            "no sh",
            "exit",
            "ip dhcp excluded-address 192.168.20.1 192.168.20.10",  # exclude range
            "ip dhcp pool DHCP_POOL",
            "network 192.168.20.0 255.255.255.0",
            "default-router 192.168.20.1",
            "dns-server 8.8.8.8",
            "exit",
            "ip dhcp pool R2", 
            "host 192.168.20.11 255.255.255.0",
            f"client-identifier {mac_addresses[0]}",
            "exit",
            "ip dhcp pool R3", 
            "host 192.168.20.12 255.255.255.0",
            f"client-identifier {mac_addresses[1]}",
            "exit" 
            
        ]

        print("\nconfiguring dhcp on r5...")
        output = net_connect.send_config_set(dhcp_config)
        print(output)

        net_connect.disconnect()
        return True
    except Exception as e:
        print(f"failed to configure dhcp on r5: {str(e)}")
        return False

#retrieve dhcp bindings
def get_dhcp_clients(r5_creds):
    try:
        time.sleep(15)
        net_connect = ConnectHandler(**r5_creds)
        output = net_connect.send_command("show ip dhcp binding")
        net_connect.disconnect()
        return output
    except Exception as e:
        print(f"failed to retrieve dhcp clients: {str(e)}")
        return None

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

    # get r4 credentials
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

    # get r5 ipv6 address
    r5_host = get_r5_ipv6_address(r4_creds)
    if not r5_host:
        print("error: could not retrieve r5 ipv6 address from r4.")
        exit()
    print(f"\nr5 ipv6 address: {r5_host}")

    # get r5 credentials
    r5_creds = router_info.get(r5_host)
    if not r5_creds:
        print(f"error: no credentials found for r5 ({r5_host}).")
        exit()

    print("\ntesting ssh connection to r5...")
    if not test_ssh_connection(r5_creds):
        print("error: unable to connect to r5 via ssh.")
        exit()
    print("successfully connected to r5.")

    # configure dhcp on r5
    if not configure_dhcp_on_r5(r5_creds, mac_addresses):
        print("error: failed to configure dhcp on r5.")
        exit()

    # get dhcp clients
    print("\nretrieving dhcp clients...")
    dhcp_clients = get_dhcp_clients(r5_creds)
    if dhcp_clients:
        print("\nlist of dhcp clients:\n")
        print(dhcp_clients)
    else:
        print("error: could not retrieve dhcp clients.")

    print("\nall tasks completed successfully.")
