#/usr/bin/env python3
from scapy.all import rdpcap, Ether, IPv6, ICMPv6EchoRequest
import json

# Имя файла с захваченным трафиком (указать актуальное имя)
PCAP_FILE = "tcpdump_capture.pcap"
OUTPUT_FILE = "mac_addr.json"

def extract_mac_ipv6(pcap_file):
    packets = rdpcap(pcap_file)
    mac_ipv6_mapping = {}

    for pkt in packets:
        if pkt.haslayer(Ether) and pkt.haslayer(IPv6) and pkt.haslayer(ICMPv6EchoRequest):
            src_mac = pkt[Ether].src
            src_ipv6 = pkt[IPv6].src
            
            if src_ipv6 not in mac_ipv6_mapping:
                mac_ipv6_mapping[src_ipv6] = src_mac

    return mac_ipv6_mapping


def save_results(data, output_file):
    """save mac address into json file"""
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Mac addresses saved in: {output_file}")


if __name__ == "__main__":
    mac_ipv6_map = extract_mac_ipv6(PCAP_FILE)
    save_results(mac_ipv6_map, OUTPUT_FILE)

  
    print("\n mac address of R2 and R3:")
    for ipv6, mac in mac_ipv6_map.items():
        print(f"IPv6: {ipv6} -> MAC: {mac}")
