"""
NetWatch AI — TLS SNI Extractor
Parses TLS ClientHello messages to extract Server Name Indication (SNI).
No decryption needed — SNI is sent in plaintext before encryption begins.
"""

import logging
from typing import Optional

logger = logging.getLogger("netwatch.capture.sni")


class SniExtractor:
    """
    Extracts domain names from TLS ClientHello SNI extension.
    
    When a client connects to an HTTPS server, the first TLS packet
    contains the target hostname in plaintext (SNI field). This gives
    us the domain name without any decryption.
    
    This is how NetWatch identifies HTTPS traffic destinations.
    """

    def __init__(self):
        self._sni_count = 0

    def process(self, packet) -> Optional[str]:
        """
        Extract SNI from a TLS ClientHello packet.
        
        Returns the domain name if found, None otherwise.
        """
        from scapy.layers.inet import TCP, IP
        from scapy.layers.tls.all import TLS, TLSClientHello, TLS_Ext_ServerName
        
        if not packet.haslayer(TCP) or not packet.haslayer(TLS):
            return None
            
        tls_layer = packet.getlayer(TLS)
        if not tls_layer.haslayer(TLSClientHello):
            return None
            
        hello = tls_layer.getlayer(TLSClientHello)
        if hello.haslayer(TLS_Ext_ServerName):
            ext = hello.getlayer(TLS_Ext_ServerName)
            if ext.servernames:
                sni = ext.servernames[0].servername.decode('utf-8')
                self._sni_count += 1
                return sni
                
        return None

    @property
    def stats(self) -> dict:
        return {"sni_extracted": self._sni_count}
