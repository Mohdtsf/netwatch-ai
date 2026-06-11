import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("netwatch.firewall.setup")

def load_base_nftables():
    """Load the base nftables configuration from base.nft."""
    base_file = Path(__file__).parent / "base.nft"
    if not base_file.exists():
        logger.error(f"Base nftables file not found at {base_file}")
        return False
        
    try:
        subprocess.run(
            ["nft", "-f", str(base_file)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Successfully loaded base nftables configuration.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to load base nftables configuration: {e.stderr}")
        return False
