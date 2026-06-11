import asyncio
import os
from unittest.mock import MagicMock
from scapy.utils import rdpcap
from src.dns_extractor import DnsExtractor
from src.sni_extractor import SniExtractor
from src.flow_assembler import FlowAssembler
from scapy.layers.inet import IP, TCP, UDP
from scapy.packet import Packet

# To test this we would need a PCAP file. We will mock the process for now 
# and use generic Scapy packet generation if a PCAP is not available.

def test_pipeline_components():
    """
    Test the extraction logic manually using synthetically created or loaded packets.
    """
    dns = DnsExtractor()
    sni = SniExtractor()
    flows = FlowAssembler(timeout=1.0)
    
    # Generate some simple synthetic packets for testing
    # In a real environment, we would use `rdpcap('sample.pcap')`
    
    # DNS packet mock (UDP 53)
    p_udp = IP(src="192.168.1.10", dst="8.8.8.8")/UDP(sport=12345, dport=53)
    
    # Web packet mock (TCP 443)
    p_tcp = IP(src="192.168.1.10", dst="1.1.1.1")/TCP(sport=54321, dport=443)
    
    dns.process(p_udp)
    sni.process(p_tcp)
    
    flows.process(p_udp)
    flows.process(p_tcp)
    
    # Emulate waiting for timeout
    import time
    time.sleep(1.1)
    
    expired = flows.flush_expired()
    assert len(expired) == 2, "Should have 2 distinct flows (UDP and TCP)"
    
    udp_flow = next(f for f in expired if f.protocol == "udp")
    tcp_flow = next(f for f in expired if f.protocol == "tcp")
    
    assert udp_flow.src_ip == "192.168.1.10"
    assert tcp_flow.src_port == 54321
