import pytest
import numpy as np
from src.features import FeatureExtractor
from src.models.isolation_forest import AnomalyDetector
from src.models.random_forest import ThreatClassifier
from src.models.hdbscan_device import DeviceFingerprinter

@pytest.fixture
def feature_extractor():
    return FeatureExtractor()

@pytest.fixture
def isolation_forest():
    detector = AnomalyDetector(contamination=0.01, threshold=-0.05)
    # Train on normal traffic centered around benign flow features
    np.random.seed(42)
    normal_data = []
    for _ in range(100):
        normal_data.append([
            100.0 + np.random.normal(0, 10),
            10.0 + np.random.normal(0, 1),
            10.0 + np.random.normal(0, 1),
            0.2 + np.random.normal(0, 0.01),
            1.0,
            0.1,
            443 / 65535,
            1.0,
            0.0,
            1.0 + np.random.normal(0, 0.1),
            1.0 + np.random.normal(0, 0.1)
        ])
    features = np.array(normal_data)
    detector.train(features)
    return detector



@pytest.fixture
def random_forest():
    classifier = ThreatClassifier()
    # Train on some mixed data
    features = np.array([
        [100.0, 10.0, 10.0, 0.2, 1.0, 0.1, 443/65535, 1.0, 0.0, 1.0, 1.0],  # Normal
        [1000000.0, 10000.0, 100.0, 0.8, 0.0, 0.9, 0.99, 1.0, 0.0, 100.0, 50.0],  # DDoS
    ] * 50)
    labels = np.array([0, 2] * 50) # 0: Normal, 2: DDoS
    classifier.train(features, labels)
    return classifier

def test_inference_pipeline(feature_extractor, isolation_forest, random_forest):
    # Benign flow
    benign_flow = {
        "src_ip": "192.168.1.5",
        "dst_port": 443,
        "duration": 5.0,
        "bytes": 500,
        "packets": 50,
        "protocol": "TCP",
        "country": "US"
    }
    
    vector = feature_extractor.extract(benign_flow)
    scores, labels = isolation_forest.predict(vector)
    
    # Depending on IF training, it should be 1 (normal)
    assert labels[0] == 1, "Benign flow should be classified as normal"
    
    # Malicious flow (e.g. huge bandwidth, unknown port, risk country)
    malicious_flow = {
        "src_ip": "192.168.1.100",
        "dst_port": 65000,
        "duration": 0.1,
        "bytes": 100000,
        "packets": 1000,
        "protocol": "TCP",
        "country": "KP"
    }
    
    # Force some state into feature extractor for connections per min
    for _ in range(100):
        feature_extractor.extract({"src_ip": "192.168.1.100", "dst_port": np.random.randint(1000, 60000)})
        
    malicious_vector = feature_extractor.extract(malicious_flow)
    scores, m_labels = isolation_forest.predict(malicious_vector)
    # Should be anomaly
    assert m_labels[0] == -1, "Malicious flow should be classified as anomaly"
    
    pred_threat = random_forest.predict(malicious_vector)[0]
    assert pred_threat != "Normal", "Anomaly should be classified as a threat"
