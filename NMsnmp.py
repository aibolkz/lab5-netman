#/usr/bin/env python3
import csv
import json
import time
from easysnmp import Session
from ipaddress import IPv6Address
from prettytable import PrettyTable
import matplotlib.pyplot as plt

# snmp configuration
SNMP_COMMUNITY = "midterm"
SNMP_PORT = 161

# load router IPs from csv
def load_router_ips(file_path):
    routers = {}
    with open(file_path, mode="r", encoding="utf8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                routers[row[0].strip()] = row[1].strip()
    return routers

# load snmp oids from csv
def load_oids(file_path):
    oids = {}
    with open(file_path, mode="r", encoding="utf8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                oids[row[0].strip()] = row[1].strip()
    return oids

# snmp walk request
def snmp_walk(ip, oid):
    result = {}
    try:
        session = Session(hostname=ip, community=SNMP_COMMUNITY, version=2, timeout=3, retries=2)
        walk_results = session.walk(oid)
        for item in walk_results:
            result[item.oid] = item.value
    except Exception as e:
        print(f"snmp walk error on {ip}: {str(e)}")
    return result

# convert raw snmp IPv6 OID output into readable IPv6 address
def format_ipv6_address(raw_oid):
    try:
        parts = raw_oid.split(".")[-16:]  # Extract last 16 values (IPv6 parts)
        ipv6 = IPv6Address(bytes(int(x) for x in parts))
        return str(ipv6)
    except Exception:
        return None

# fetch snmp data from all routers
def fetch_snmp_data(router_ips, oids):
    snmp_data = {}

    for router, ip in router_ips.items():
        print(f"\nfetching snmp data from {router} ({ip})...")

        ipv4_addresses = list(snmp_walk(ip, oids["OID_IF_IPV4"]).values())
        raw_ipv6_addresses = snmp_walk(ip, oids["OID_IF_IPV6"])
        raw_interface_status = snmp_walk(ip, oids["OID_IF_STATUS"])
        cpu_utilization_raw = snmp_walk(ip, oids["OID_CPU_UTILIZATION"])

        # convert ipv6 to readable format and take only the first address per interface
        ipv6_addresses = {}
        for oid, value in raw_ipv6_addresses.items():
            ipv6_addr = format_ipv6_address(oid)
            if ipv6_addr and value not in ipv6_addresses:
                ipv6_addresses[value] = ipv6_addr

        # convert interface status (1=up, 2=down)
        interface_status = {k.split(".")[-1]: "up" if v == "1" else "down" for k, v in raw_interface_status.items()}

        # validate cpu data using snmpwalk results
        cpu_utilization = "N/A"
        if cpu_utilization_raw:
            # Try to extract the last value from the snmpwalk result
            try:
                cpu_utilization = [value for value in cpu_utilization_raw.values()][-1]  # Last value in the list
                cpu_utilization = f"{cpu_utilization}%" if cpu_utilization.isdigit() else "N/A"
            except Exception as e:
                cpu_utilization = "N/A"

        snmp_data[router] = {
            "ipv4_addresses": ipv4_addresses,
            "ipv6_addresses": list(ipv6_addresses.values()),  # Only first IPv6 address per interface
            "interface_status": interface_status,
            "cpu_utilization": cpu_utilization
        }

    return snmp_data

#snmp  to json file
def save_snmp_data(snmp_data, filename="snmp_data.txt"):
    with open(filename, "w", encoding="utf8") as file:
        json.dump(snmp_data, file, indent=4)
    print(f"\nsnmp data saved to {filename}")

#snmp data in table
def display_snmp_data(snmp_data):
    table = PrettyTable(["Router", "IPv4 Addresses", "IPv6 Addresses", "Interfaces", "CPU Utilization"])
    
    for router, data in snmp_data.items():
        ipv4 = ", ".join(data["ipv4_addresses"]) if data["ipv4_addresses"] else "None"
        ipv6 = ", ".join(data["ipv6_addresses"]) if data["ipv6_addresses"] else "None"
        interfaces = ", ".join(f"{k}: {v}" for k, v in data["interface_status"].items())
        cpu = data["cpu_utilization"] if data["cpu_utilization"] else "N/A"
        table.add_row([router, ipv4, ipv6, interfaces, cpu])

    print("\nSNMP Data Summary:\n")
    print(table)

#cpu utilization for 2 minutes
#value for testing is 60 and 10 secs
def monitor_cpu(router_ip, oid, duration=60, interval=10):
    print("\nmonitoring cpu utilization of r1 for 2 minutes...")
    cpu_data = []
    timestamps = []

    start_time = time.time()
    while time.time() - start_time < duration:
        cpu_value = snmp_walk(router_ip, oid)  # Using snmpwalk for continuous data
        cpu_value = [value for value in cpu_value.values()][-1]  # Extract the last value

        try:
            cpu_int = int(cpu_value)
            if cpu_int >= 0:
                elapsed_time = round(time.time() - start_time, 1)
                cpu_data.append(cpu_int)
                timestamps.append(elapsed_time)
                print(f"time: {elapsed_time}s, cpu: {cpu_int}%")
        except (ValueError, TypeError):
            print(f"time: {round(time.time() - start_time, 1)}s, no valid CPU data")
        
        time.sleep(interval)

    # Ensure the graph is generated even if CPU data is invalid or zero
    if not cpu_data:  # If no valid CPU data was collected, set data to zero
        cpu_data = [0] * int(duration / interval)  # Create a list of zeros for the entire duration
        timestamps = [i * interval for i in range(len(cpu_data))]  # Create timestamps for the duration

    # Plot and save the CPU utilization graph
    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, cpu_data, marker="o", linestyle="-", color="b")
    plt.xlabel("Time (seconds)")
    plt.ylabel("CPU Utilization (%)")
    plt.title("CPU Utilization of R1 Over Time")
    plt.grid()
    plt.savefig("cpu_utilization.jpg")
    print("\ncpu utilization graph saved to cpu_utilization.jpg")


#MAIN
if __name__ == "__main__":
    router_ips = load_router_ips("snmp_routers.csv")
    oids = load_oids("oid_commands.csv")

    snmp_data = fetch_snmp_data(router_ips, oids)

    # save to json file
    save_snmp_data(snmp_data)

    # display formatted output
    display_snmp_data(snmp_data)

    # monitor cpu utilization of R1
    if "R1" in router_ips:
        monitor_cpu(router_ips["R1"], oids["OID_CPU_UTILIZATION"])
