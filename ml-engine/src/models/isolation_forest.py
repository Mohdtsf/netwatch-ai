"""
NetWatch AI — Isolation Forest Anomaly Detector
Detects unusual network traffic patterns using unsupervised learning.
"""

import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger("netwatch.ml.isolation_forest")

MODEL_PATH = os.getenv("ISOLATION_FOREST_MODEL_PATH", "/app/data/ml-models/isolation_forest.pkl")



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
            self._scaler = saved.get("scaler")
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
        """
        logger.info("Training Isolation Forest...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        from sklearn.ensemble import IsolationForest
        self._model = IsolationForest(n_estimators=100, contamination=self.contamination, random_state=42)
        self._model.fit(features)
        
        import joblib
        joblib.dump({"model": self._model}, MODEL_PATH)
        self._loaded = True
        logger.info("✅ Isolation Forest trained and saved")
        
        try:
            import mlflow
            import mlflow.sklearn
            if mlflow.active_run():
                mlflow.sklearn.log_model(self._model, "isolation_forest")
        except ImportError:
            pass

    def predict(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Score flows for anomalies.
        
        Returns:
            (scores, labels) where scores < threshold are anomalies
        """
        if not self._loaded:
            n = len(features)
            return np.zeros(n), np.ones(n)
            
        scores = self._model.decision_function(features)
        labels = np.where(scores < self.threshold, -1, 1)
        return scores, labels

    @property
    def is_loaded(self) -> bool:
        return self._loaded
