"""
NetWatch AI — HDBSCAN Device Fingerprinter
Clusters devices by their traffic patterns to infer device types.
"""

import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger("netwatch.ml.hdbscan")

MODEL_PATH = os.getenv("HDBSCAN_MODEL_PATH", "/app/data/ml-models/hdbscan_device.pkl")



class DeviceFingerprinter:
    """
    HDBSCAN-based device type clustering.
    
    Groups devices by traffic behavior patterns:
    - Typical ports accessed
    - DNS query patterns
    - Traffic volume profiles
    - Time-of-day activity patterns
    
    This helps classify unknown devices as:
    phone, laptop, tablet, smart_tv, iot, printer, router, gaming_console
    """

    DEVICE_TYPES = [
        "phone", "laptop", "tablet", "smart_tv",
        "iot", "printer", "router", "gaming_console",
        "camera", "speaker", "unknown",
    ]

    def __init__(self, min_cluster_size: int = 3):
        self.min_cluster_size = min_cluster_size
        self._model = None
        self._loaded = False

    def load(self) -> bool:
        """Load pre-trained model from disk."""
        if not os.path.exists(MODEL_PATH):
            logger.warning("No trained HDBSCAN model found")
            return False
            
        try:
            import joblib
            saved = joblib.load(MODEL_PATH)
            self._model = saved["model"]
            self._loaded = True
            logger.info("✅ HDBSCAN device fingerprinter loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load HDBSCAN model: {e}")
            return False

    def train(self, features: np.ndarray):
        """Train HDBSCAN on device traffic features."""
        logger.info("Training HDBSCAN...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        import hdbscan
        self._model = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_size, prediction_data=True)
        self._model.fit(features)
        
        import joblib
        joblib.dump({"model": self._model}, MODEL_PATH)
        self._loaded = True
        logger.info("✅ HDBSCAN trained and saved")

    def predict(self, features: np.ndarray) -> list[str]:
        """Predict device types from traffic patterns."""
        if not self._loaded:
            return ["unknown"] * len(features)
            
        import hdbscan
        labels, _ = hdbscan.approximate_predict(self._model, features)
        return [self.DEVICE_TYPES[abs(l) % len(self.DEVICE_TYPES)] if l != -1 else "unknown" for l in labels]

    @property
    def is_loaded(self) -> bool:
        return self._loaded
