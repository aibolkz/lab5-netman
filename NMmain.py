import NMtcpdump
import NMdhcp
import NMsnmp
import NMgithub

def main():
    #extract MAC addresses from IPv6 addresses
    print("Extracting MAC addresses from IPv6 addresses...")
    mac_ipv6_map = NMtcpdump.extract_mac_ipv6("c1_from_r2_r3.pcap")
    NMtcpdump.save_mapping(mac_ipv6_map, "mac_addr.json")
    
    print("\nExtracted MAC from IPv6 address:")
    for ipv6, mac in mac_ipv6_map.items():
        print(f"IPv6: {ipv6} is MAC: {mac}")
    


    #configure DHCP on R5
    print("\nConfiguring DHCP on R5...")
    router_info = NMdhcp.load_router_info("routers_info.csv")
    mac_addresses = NMdhcp.load_mac_addresses()
    


    if not router_info or not mac_addresses:
        print("Error: No router data or MAC addresses found.")
        return
    


    #get R4 credentials
    r4_creds = router_info.get("db8:1::2", None)
    if not r4_creds:
        print("Error: Could not find R4 credentials.")
        return
    
    #get R5 IPv6 address from R4
    r5_ipv6 = NMdhcp.get_r5_ipv6_address(r4_creds)
    if not r5_ipv6:
        print("Error: Could not get R5 IPv6 address from R4.")
        return

    #get R5 credentials and configure DHCP
    r5_creds = router_info.get(r5_ipv6)
    if not r5_creds:
        print(f"Error: No credentials found for R5 ({r5_ipv6}).")
        return
    
    if not NMdhcp.configure_dhcp_on_r5(r5_creds, mac_addresses):
        print("Error: Failed to configure DHCP on R5.")
        return
    
    # 3 get SNMP data
    print("\nFetching SNMP data...")
    router_ips = NMsnmp.load_router_ips("snmp_routers.csv")
    oids = NMsnmp.load_oids("oid_commands.csv")
    snmp_data = NMsnmp.fetch_snmp_data(router_ips, oids)
    
    #saving SNMP data to a file
    NMsnmp.save_snmp_data(snmp_data)
    
    #Display SNMP data in table
    NMsnmp.display_snmp_data(snmp_data)
    
    #gitHub section
    print("\nPushing changes to GitHub...")
    NMgithub.main()

if __name__ == "__main__":
    main()
