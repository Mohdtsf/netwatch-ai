"""
NetWatch AI — Random Forest Threat Classifier
Classifies detected anomalies into threat categories.
"""

import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger("netwatch.ml.random_forest")

MODEL_PATH = "/app/data/ml-models/random_forest.pkl"

THREAT_LABELS = [
    "Normal",
    "PortScan",
    "DDoS",
    "BruteForce",
    "Exfiltration",
    "C2Communication",
    "Reconnaissance",
    "MalwareDownload",
]


class ThreatClassifier:
    """
    Random Forest classifier for threat type identification.
    
    Once the Isolation Forest detects an anomaly, this model
    classifies it into specific threat categories:
    - PortScan
    - DDoS  
    - BruteForce
    - Exfiltration
    - C2Communication
    - Reconnaissance
    - MalwareDownload
    
    Trained on NSL-KDD and CICIDS datasets, adapted for home network patterns.
    """

    def __init__(self):
        self._model = None
        self._scaler = None
        self._loaded = False

    def load(self) -> bool:
        """Load pre-trained model from disk."""
        if not os.path.exists(MODEL_PATH):
            logger.warning("No trained threat classifier found")
            return False

        try:
            import joblib
            saved = joblib.load(MODEL_PATH)
            self._model = saved["model"]
            self._scaler = saved["scaler"]
            self._loaded = True
            logger.info("✅ Random Forest classifier loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def predict(self, features: np.ndarray) -> list[str]:
        """
        Classify anomalous flows into threat types.
        TODO Phase 8: Implement inference.
        """
        return ["Normal"] * len(features)  # Stub

    @property
    def is_loaded(self) -> bool:
        return self._loaded
