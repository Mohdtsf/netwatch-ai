"""
NetWatch AI — DNS Blocklist Updater
Background task to download, filter, and generate categorized CoreDNS blocklists.
Supports the comprehensive suite of HaGeZi lists with memory and lookup optimization.
"""

import logging
import httpx
import os
import time
import json
import asyncio

logger = logging.getLogger("netwatch.dns.blocklist")

CONFIG_FILE = os.environ.get("BLOCKLIST_CONFIG", "data/blocklist_config.json")
BLOCKLIST_DIR = os.environ.get("BLOCKLIST_DIR", "/app/coredns/blocklists")
if not os.path.exists("/app") and not os.environ.get("BLOCKLIST_DIR"):
    # Fallback for local testing outside docker
    BLOCKLIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../coredns/blocklists"))
    
ACTIVE_CONF_FILE = os.path.join(BLOCKLIST_DIR, "active_blocklists.conf")

# Comprehensive HaGeZi Blocklist Dictionary (Using 'domains' format for easy whitelisting)
AVAILABLE_LISTS = {
    # ── Core Multi Lists (Protection Levels) ──
    "multi_light": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/light.txt", "desc": "Light protection. No restrictions."},
    "multi_normal": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/multi.txt", "desc": "All-round protection."},
    "multi_pro": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/pro.txt", "desc": "Extended protection (Recommended)."},
    "multi_pro_plus": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/pro.plus.txt", "desc": "Maximum protection."},
    "multi_ultimate": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/ultimate.txt", "desc": "Ultimate aggressive protection."},
    
    # ── Optional Security & Anti-Abuse ──
    "fake": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/fake.txt", "desc": "Fake stores, rip-offs, cost traps."},
    "popup_ads": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/popupads.txt", "desc": "Annoying pop-up ads."},
    "threat_intel": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/tif.txt", "desc": "Threat Intelligence Feeds (Malware, Phishing, C2)."},
    "nrd_7_days": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/nrd7.txt", "desc": "Newly Registered Domains (last 7 days). High FP risk."},
    "bypass_prevention": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/doh-vpn-proxy-bypass.txt", "desc": "Prevent DNS bypass via VPN/TOR/Proxies/DoH."},
    "safesearch": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/nosafesearch.txt", "desc": "Block search engines missing Safesearch."},
    "dyndns": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/dyndns.txt", "desc": "Block dynamic DNS providers (used in phishing)."},
    "badware_hoster": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/hoster.txt", "desc": "Block hosts known for badware."},
    "url_shortener": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/urlshortener.txt", "desc": "Block URL/Link shorteners."},
    
    # ── Optional Content Filtering ──
    "anti_piracy": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/anti.piracy.txt", "desc": "Protect against piracy platforms."},
    "gambling": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/gambling.txt", "desc": "Block gambling platforms."},
    "social_networks": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/social.txt", "desc": "Block social media networks."},
    "nsfw": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/nsfw.txt", "desc": "Block adult/NSFW content."},
    
    # ── Native Trackers (Devices & OS) ──
    "native_amazon": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/native.amazon.txt", "desc": "Amazon trackers."},
    "native_apple": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/native.apple.txt", "desc": "Apple iOS/macOS trackers."},
    "native_microsoft": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/native.winoffice.txt", "desc": "Microsoft Windows/Office trackers."},
    "native_tiktok": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/native.tiktok.txt", "desc": "TikTok trackers & fingerprinting."},
    "native_huawei": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/native.huawei.txt", "desc": "Huawei trackers."},
    "native_samsung": {"url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/native.samsung.txt", "desc": "Samsung trackers."}
}

# Default configuration
DEFAULT_CONFIG = {
    "enabled_lists": [
        "multi_pro",
        "threat_intel",
        "fake",
        "popup_ads"
    ],
    "custom_urls": [],
    "whitelist": [
        # Explicit user bypasses will go here
        "example.com"
    ],
    "blacklist": [
        # Custom manual blocks
    ]
}

def load_config():
    """Load configuration from JSON."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading config, using defaults: {e}")
        return DEFAULT_CONFIG

async def download_and_process_list(client, name, url, whitelist):
    """
    Downloads a domain list, filters out whitelisted items, 
    and saves to a specific CoreDNS hosts file.
    """
    try:
        logger.debug(f"Downloading {name} blocklist from {url}...")
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        output_file = os.path.join(BLOCKLIST_DIR, f"{name}.hosts")
        count = 0
        
        with open(output_file, "w") as f:
            f.write(f"# NetWatch AI Blocklist: {name}\n")
            f.write(f"# Source: {url}\n\n")
            
            for line in response.text.splitlines():
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue
                
                # 'domains' format is a simple domain per line
                domain = line.split()[0].lower()
                
                if domain == "localhost" or domain in whitelist:
                    continue
                    
                # Format for CoreDNS hosts plugin: "0.0.0.0 domain"
                f.write(f"0.0.0.0 {domain}\n")
                count += 1
                
        logger.info(f"✅ Processed {name}: {count} domains (filtered {len(whitelist)}).")
        return name, output_file
        
    except Exception as e:
        logger.error(f"Failed to fetch {name} blocklist from {url}: {e}")
        return None, None

async def update_blocklists():
    """
    Fetch all active lists and write them as separate categorized files.
    Generate a config file for CoreDNS to import.
    """
    logger.info("🔄 Starting categorized DNS blocklist update...")
    start_time = time.time()
    
    os.makedirs(BLOCKLIST_DIR, exist_ok=True)
    config = load_config()
    whitelist = set(config.get("whitelist", []))
    blacklist = set(config.get("blacklist", []))
    enabled_lists = config.get("enabled_lists", [])
    
    tasks = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for name in enabled_lists:
            if name in AVAILABLE_LISTS:
                url = AVAILABLE_LISTS[name]["url"]
                tasks.append(download_and_process_list(client, name, url, whitelist))
                
        for idx, url in enumerate(config.get("custom_urls", [])):
            tasks.append(download_and_process_list(client, f"custom_{idx}", url, whitelist))
            
        results = await asyncio.gather(*tasks)

    # Process explicit user blacklist
    if blacklist:
        manual_file = os.path.join(BLOCKLIST_DIR, "manual_blacklist.hosts")
        with open(manual_file, "w") as f:
            f.write("# NetWatch AI Manual Blacklist\n\n")
            for domain in blacklist:
                if domain not in whitelist:
                    f.write(f"0.0.0.0 {domain}\n")
        results.append(("manual_blacklist", manual_file))
        logger.info(f"✅ Processed Manual Blacklist: {len(blacklist)} domains.")

    # Generate the import configuration file for CoreDNS
    valid_files = [res[1] for res in results if res[1] is not None]
    
    try:
        # CoreDNS's hosts plugin struggles to correctly load multiple large files simultaneously.
        # We merge all valid files into a single `combined.hosts` for optimal performance.
        combined_file = os.path.join(BLOCKLIST_DIR, "combined.hosts")
        total_domains = 0
        with open(combined_file, "w") as combined_f:
            combined_f.write("# NetWatch AI Combined Blocklist\n")
            combined_f.write(f"# Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for file_path in valid_files:
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        content = f.read()
                        combined_f.write(content)
                        combined_f.write("\n")
        
        # Create an empty active_blocklists.conf to ensure it exists
        if not os.path.exists(ACTIVE_CONF_FILE):
             open(ACTIVE_CONF_FILE, 'a').close()
             
        with open(ACTIVE_CONF_FILE, "w") as f:
            f.write("# Auto-generated CoreDNS blocklist imports\n")
            f.write(f"# Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if valid_files:
                # Tell CoreDNS to load only the combined file
                container_path = "/etc/coredns/blocklists/combined.hosts"
                f.write(f"hosts {container_path} {{\n    fallthrough\n}}\n")
                
        logger.info(f"🎉 Blocklist update complete. {len(valid_files)} categories active and merged into combined.hosts. ({time.time() - start_time:.2f}s)")
        
        # Trigger graceful reload
        from src.dns.rule_manager import reload_coredns
        reload_coredns()
        
    except Exception as e:
        logger.error(f"Failed to generate CoreDNS import config: {e}")

if __name__ == "__main__":
    # Setup basic logging for testing standalone
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(update_blocklists())
