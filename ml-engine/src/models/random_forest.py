"""
NetWatch AI — Random Forest Threat Classifier
Classifies detected anomalies into threat categories.
"""

import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger("netwatch.ml.random_forest")

MODEL_PATH = os.getenv("RANDOM_FOREST_MODEL_PATH", "/app/data/ml-models/random_forest.pkl")


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
            self._scaler = saved.get("scaler")
            self._loaded = True
            logger.info("✅ Random Forest classifier loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def train(self, features: np.ndarray, labels: np.ndarray):
        """Train Random Forest Threat Classifier."""
        logger.info("Training Random Forest Threat Classifier...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        from sklearn.ensemble import RandomForestClassifier
        self._model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
        self._model.fit(features, labels)
        
        import joblib
        joblib.dump({"model": self._model}, MODEL_PATH)
        self._loaded = True
        logger.info("✅ Random Forest trained and saved")
        
        try:
            import mlflow
            import mlflow.sklearn
            if mlflow.active_run():
                mlflow.sklearn.log_model(self._model, "random_forest")
        except ImportError:
            pass

    def predict(self, features: np.ndarray) -> list[str]:
        """Classify anomalous flows into threat types."""
        if not self._loaded:
            return ["Normal"] * len(features)
            
        predictions = self._model.predict(features)
        # Handle cases where label index is out of bounds just in case
        return [THREAT_LABELS[i] if i < len(THREAT_LABELS) else "Unknown" for i in predictions]

    @property
    def is_loaded(self) -> bool:
        return self._loaded
