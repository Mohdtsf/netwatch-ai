import os
import sys
import logging
import numpy as np
from pathlib import Path

# Add src to python path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("bootstrap")

def ensure_dirs():
    # Make sure we use the local data directory when running outside docker
    local_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ml-models"))
    os.makedirs(local_data_dir, exist_ok=True)
    
    # Override the hardcoded docker paths to point to the local filesystem
    os.environ["ISOLATION_FOREST_MODEL_PATH"] = os.path.join(local_data_dir, "isolation_forest.pkl")
    os.environ["RANDOM_FOREST_MODEL_PATH"] = os.path.join(local_data_dir, "random_forest.pkl")
    os.environ["HDBSCAN_MODEL_PATH"] = os.path.join(local_data_dir, "hdbscan_device.pkl")

# Setup environment before importing models
ensure_dirs()

from models.isolation_forest import AnomalyDetector, MODEL_PATH as IF_PATH
from models.random_forest import ThreatClassifier, MODEL_PATH as RF_PATH
from models.hdbscan_device import DeviceFingerprinter, MODEL_PATH as HD_PATH

def generate_isolation_forest():
    logger.info("Generating synthetic data for Isolation Forest...")
    # Generate ~5000 normal flows
    # Features: bytes/sec, pkts/sec, byte_ratio, port_entropy, well_known, geo, norm_port, tcp, udp, conn/min, unq_ports
    normal_data = []
    for _ in range(5000):
        normal_data.append([
            np.random.uniform(100, 5000),     # bytes/sec
            np.random.uniform(5, 50),         # pkts/sec
            np.random.uniform(50, 150),       # bytes/packet
            0.2,                              # port entropy (low for well known)
            1.0,                              # is well known port
            0.1,                              # geo risk (low)
            443 / 65535,                      # normalized port
            1.0,                              # tcp
            0.0,                              # udp
            np.random.uniform(1, 10),         # conn per min
            np.random.uniform(1, 3)           # unique ports
        ])
    
    features = np.array(normal_data)
    detector = AnomalyDetector()
    detector.train(features)
    logger.info("Isolation Forest successfully bootstrapped.")

def generate_random_forest():
    logger.info("Generating synthetic data for Random Forest...")
    
    X = []
    y = []
    
    # Normal (Label 0)
    for _ in range(2000):
        X.append([np.random.uniform(100, 5000), 10.0, 100.0, 0.2, 1.0, 0.1, 443/65535, 1.0, 0.0, 5.0, 2.0])
        y.append(0)
        
    # PortScan (Label 1)
    for _ in range(500):
        X.append([np.random.uniform(10, 100), 2.0, 50.0, 0.9, 0.0, 0.2, np.random.uniform(0.1, 0.9), 1.0, 0.0, 100.0, 50.0])
        y.append(1)
        
    # DDoS (Label 2)
    for _ in range(500):
        X.append([np.random.uniform(100000, 5000000), 5000.0, 1000.0, 0.1, 1.0, 0.6, 80/65535, 0.0, 1.0, 500.0, 2.0])
        y.append(2)
        
    # BruteForce (Label 3)
    for _ in range(300):
        X.append([500.0, 10.0, 50.0, 0.1, 1.0, 0.5, 22/65535, 1.0, 0.0, 50.0, 1.0])
        y.append(3)
        
    features = np.array(X)
    labels = np.array(y)
    
    classifier = ThreatClassifier()
    classifier.train(features, labels)
    logger.info("Random Forest successfully bootstrapped.")

def generate_hdbscan():
    logger.info("Generating synthetic data for HDBSCAN...")
    # Generate clear clusters of devices based on port usage and bandwidth
    features = []
    
    # Phones (high 443 usage, varying bandwidth)
    for _ in range(100):
        features.append([np.random.normal(500, 100), 1.0, 0.0])
        
    # IoT Devices (low bandwidth, 80/443, constant connections)
    for _ in range(100):
        features.append([np.random.normal(10, 2), 0.0, 1.0])
        
    # Laptops (high bandwidth, bursts)
    for _ in range(100):
        features.append([np.random.normal(2000, 500), 1.0, 1.0])
        
    features = np.array(features)
    
    fingerprinter = DeviceFingerprinter()
    fingerprinter.train(features)
    logger.info("HDBSCAN successfully bootstrapped.")

if __name__ == "__main__":
    logger.info("Starting ML Engine Bootstrap...")
    ensure_dirs()
    
    # Actually run the initial generation scripts
    generate_isolation_forest()
    generate_random_forest()
    generate_hdbscan()
    
    logger.info("Bootstrap complete! The .pkl files have been saved to data/ml-models/")
