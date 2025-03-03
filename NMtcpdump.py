from scapy.all import rdpcap, Ether, IPv6
import json

PCAP_FILE = "c1_from_r2_r3.pcap"
OUTPUT_FILE = "mac_addr.json"

def extract_mac_ipv6(pcap_file):
    """Extracts IPv6 addresses starting with 2001:1111:2222:3333 and converts them to MAC addresses."""
    packets = rdpcap(pcap_file)
    mac_ipv6_mapping = {}

    for pkt in packets:
        if pkt.haslayer(Ether) and pkt.haslayer(IPv6):
            src_ipv6 = pkt[IPv6].src

            # Process only IPv6 addresses starting with "2001:1111:2222:3333"
            if src_ipv6.lower().startswith("2001:1111:2222:3333"):
                mac_address = reverse_eui64(src_ipv6)
                if mac_address:  # Store valid MACs
                    mac_ipv6_mapping[src_ipv6] = mac_address

    return mac_ipv6_mapping

def reverse_eui64(ipv6):
    """Converts an EUI-64-based IPv6 address back to its MAC address."""
    parts = ipv6.split(":")

    # Ensure IPv6 address has at least 8 segments
    while len(parts) < 8:
        parts.append("0000")

    # Extract last 64 bits (EUI-64 interface identifier)
    eui64_segments = parts[4:8]  # Extract segments after the first 4 (EUI-64 portion)

    # Expand zero-compressed addresses
    eui64_segments = [segment.zfill(4) for segment in eui64_segments]

    # Ensure we have exactly 4 segments
    if len(eui64_segments) != 4:
        print(f"Skipping invalid IPv6 address: {ipv6}")
        return None

    # Join segments as a single string
    eui64 = "".join(eui64_segments)

    # Ensure 'FFFE' is in the correct place
    if eui64[6:10].lower() != "fffe":
        print(f"Skipping non-EUI-64 IPv6 address: {ipv6}")
        return None

    # Extract MAC address components (remove FFFE)
    mac = [
        eui64[0:2], eui64[2:4],  # First byte
        eui64[4:6], eui64[10:12],  # Middle bytes (excluding FFFE)
        eui64[12:14], eui64[14:16]  # Last bytes
    ]

    # Ensure we have 6 elements to avoid IndexError
    if len(mac) != 6:
        print(f"Skipping malformed EUI-64 IPv6 address: {ipv6}")
        return None

    # Convert first octet and flip the 7th bit
    first_octet = int(mac[0], 16)
    first_octet ^= 0b00000010  # Flip the bit

    # Format MAC address
    mac[0] = f"{first_octet:02X}"
    return f"{mac[0]}:{mac[1]}:{mac[2]}:{mac[3]}:{mac[4]}:{mac[5]}"

def save_mapping(data, output_file):
    """saving extracted MACs in json file """
    mac_only_list = list(data.values())  # Extract only MAC addresses
    with open(output_file, "w") as f:
        json.dump(mac_only_list, f, indent=4)
    print(f"MAC addresses saved to {output_file}")

if __name__ == "__main__":
    mac_ipv6_map = extract_mac_ipv6(PCAP_FILE)
    save_mapping(mac_ipv6_map, OUTPUT_FILE)

    print("\nExtracted Mac from ipv6 address")
    for ipv6, mac in mac_ipv6_map.items():
        print(f"IPv6: {ipv6} is MAC: {mac}")
