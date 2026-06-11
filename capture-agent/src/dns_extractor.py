"""
NetWatch AI — DNS Query Extractor
Parses DNS packets to extract query names and build IP-to-domain cache.
"""

import logging
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger("netwatch.capture.dns")


class DnsExtractor:
    """
    Extracts DNS queries from captured packets.
    
    Maintains an LRU cache of IP → domain mappings (from DNS responses)
    so that subsequent TCP/UDP flows can be enriched with domain names.
    """

    def __init__(self, cache_size: int = 10_000):
        self.cache_size = cache_size
        self._ip_to_domain: OrderedDict[str, str] = OrderedDict()
        self._query_count = 0
        self._response_count = 0

    def process(self, packet) -> Optional[dict]:
        """
        Process a DNS packet.
        
        Returns a dict with query info if this is a DNS query, None otherwise.
        """
        from scapy.layers.dns import DNS, DNSRR, DNSQR
        from scapy.layers.inet import IP

        if not packet.haslayer(DNS):
            return None

        ip_layer = packet.getlayer(IP)
        if not ip_layer:
            return None

        dns_layer = packet.getlayer(DNS)
        
        # Check if it's a DNS response
        if dns_layer.qr == 1 and dns_layer.ancount > 0:
            self._response_count += 1
            for i in range(dns_layer.ancount):
                answer = dns_layer.an[i]
                if isinstance(answer, DNSRR) and answer.type == 1: # A record
                    domain = answer.rrname.decode('utf-8').rstrip('.')
                    ip = answer.rdata
                    self._cache_put(ip, domain)
                    
        # Check if it's a DNS query
        elif dns_layer.qr == 0 and dns_layer.qdcount > 0:
            self._query_count += 1
            query = dns_layer.qd[0]
            if isinstance(query, DNSQR):
                domain = query.qname.decode('utf-8').rstrip('.')
                return {"domain": domain, "src_ip": ip_layer.src}

        return None

    def lookup(self, ip: str) -> Optional[str]:
        """Look up a domain name for an IP address from the cache."""
        return self._ip_to_domain.get(ip)

    def _cache_put(self, ip: str, domain: str):
        """Add an IP → domain mapping to the LRU cache."""
        if ip in self._ip_to_domain:
            self._ip_to_domain.move_to_end(ip)
        self._ip_to_domain[ip] = domain
        if len(self._ip_to_domain) > self.cache_size:
            self._ip_to_domain.popitem(last=False)

    @property
    def stats(self) -> dict:
        return {
            "cache_size": len(self._ip_to_domain),
            "queries": self._query_count,
            "responses": self._response_count,
        }
