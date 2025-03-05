#!/usr/bin/env python3
import csv
import json
import time
from prettytable import PrettyTable
from easysnmp import Session

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

# load SNMP OIDs from csv
def load_oids(file_path):
    oids = {}
    with open(file_path, mode="r", encoding="utf8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                oids[row[0].strip()] = row[1].strip()
    return oids

# snmp get request
def snmp_get(ip, oid):
    try:
        session = Session(hostname=ip, community=SNMP_COMMUNITY, version=2)
        result = session.get(oid)
        return result.value
    except Exception as e:
        print(f"SNMP GET error on {ip}: {str(e)}")
        return None

# snmp walk request
def snmp_walk(ip, oid):
    result = {}
    try:
        session = Session(hostname=ip, community=SNMP_COMMUNITY, version=2)
        walk_results = session.walk(oid)
        for item in walk_results:
            result[item.oid] = item.value
    except Exception as e:
        print(f"SNMP WALK error on {ip}: {str(e)}")
    return result

# load routers and OIDs
router_ips = load_router_ips("snmp_routers.csv")
oids = load_oids("oid_commands.csv")

snmp_data = {}

for router, ip in router_ips.items():
    print(f"\nFetching SNMP data from {router} ({ip})...")

    ipv4_addresses = snmp_walk(ip, oids.get("OID_IF_IPV4"))
    ipv6_addresses = snmp_walk(ip, oids.get("OID_IF_IPV6"))
    interface_status = snmp_walk(ip, oids.get("OID_IF_STATUS"))
    cpu_utilization = snmp_get(ip, oids.get("OID_CPU_UTILIZATION"))

    snmp_data[router] = {
        "ipv4_addresses": ipv4_addresses,
        "ipv6_addresses": ipv6_addresses,
        "interface_status": interface_status,
        "cpu_utilization": cpu_utilization
    }

# save SNMP data to JSON file
with open("snmp_data.json", "w") as file:
    json.dump(snmp_data, file, indent=4)

print("\nSNMP data saved to snmp_data.json")

# monitoring CPU utilization of R1 continuously for 2 minutes
cpu_table = PrettyTable()
cpu_table.field_names = ["Time (seconds)", "CPU Utilization (%)"]
start_time = time.time()

print("\nMonitoring CPU utilization of R1 for 2 minutes...")
while time.time() - start_time < 120:
    cpu_util = snmp_get(router_ips["R1"], oids["OID_CPU_UTILIZATION"])
    timestamp = round(time.time() - start_time, 1)

    if cpu_util:
        cpu_table.add_row([timestamp, cpu_util])
        print(cpu_table)

    time.sleep(5)

print("\nCPU Utilization Data Table:")
print(cpu_table)
