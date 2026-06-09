"""
NetWatch AI — Isolation Forest Anomaly Detector
Detects unusual network traffic patterns using unsupervised learning.
"""

import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger("netwatch.ml.isolation_forest")

MODEL_PATH = "/app/data/ml-models/isolation_forest.pkl"


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detection for network flows.
    
    The model learns normal traffic patterns from your network and
    flags flows that deviate significantly. No labels needed —
    it's trained entirely on normal traffic (unsupervised).
    
    Features used:
    - bytes_per_second
    - packets_per_second
    - byte_ratio (outbound/inbound)
    - port_entropy
    - connections_per_minute
    - unique_ports_per_minute
    - geo_risk_score
    
    Operates in O(n) time and uses ~30 MB RAM.
    """

    def __init__(self, contamination: float = 0.1, threshold: float = -0.2):
        self.contamination = contamination
        self.threshold = threshold
        self._model = None
        self._scaler = None
        self._loaded = False

    def load(self) -> bool:
        """Load a pre-trained model from disk."""
        if not os.path.exists(MODEL_PATH):
            logger.warning("No trained model found. Train first with .train()")
            return False

        try:
            import joblib
            saved = joblib.load(MODEL_PATH)
            self._model = saved["model"]
            self._scaler = saved["scaler"]
            self._loaded = True
            logger.info("✅ Isolation Forest model loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def train(self, features: np.ndarray):
        """
        Train the Isolation Forest on normal traffic data.
        
        Args:
            features: 2D numpy array of shape (n_samples, n_features)
        TODO Phase 8: Implement training pipeline.
        """
        pass

    def predict(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Score flows for anomalies.
        
        Returns:
            (scores, labels) where scores < threshold are anomalies
        TODO Phase 8: Implement inference.
        """
        n = len(features)
        return np.zeros(n), np.ones(n)  # All normal (stub)

    @property
    def is_loaded(self) -> bool:
        return self._loaded
