"""
NetWatch AI — NATS Consumer for ML Engine
Consumes enriched flows from NATS and runs ML inference.
"""

import logging
import os
import json
from nats.aio.client import Client as NATS
from nats.js.errors import NotFoundError

from .features import FeatureExtractor
from .models.isolation_forest import AnomalyDetector
from .models.random_forest import ThreatClassifier
from .threat_intel import ThreatIntelManager

logger = logging.getLogger("netwatch.ml.nats_consumer")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


class MLNatsConsumer:
    """
    Consumes enriched flow data from NATS JetStream and runs:
    1. Feature extraction
    2. Isolation Forest anomaly scoring
    3. Random Forest threat classification (if anomaly detected)
    4. Threat intel IP/domain checking
    5. Alert publishing to NATS alerts topic
    """

    def __init__(self, threat_intel: ThreatIntelManager, url: str = NATS_URL):
        self.url = url
        self._nc = NATS()
        self._js = None
        self._sub = None
        
        self.features = FeatureExtractor()
        self.anomaly_detector = AnomalyDetector()
        self.threat_classifier = ThreatClassifier()
        self.threat_intel = threat_intel

    async def start(self):
        """Connect to NATS and subscribe to enriched-flows."""
        try:
            await self._nc.connect(self.url)
            self._js = self._nc.jetstream()
            
            # Load models
            self.anomaly_detector.load()
            self.threat_classifier.load()
            
            # Ensure streams exist
            try:
                await self._js.stream_info("netwatch_flows")
            except NotFoundError:
                await self._js.add_stream(name="netwatch_flows", subjects=["raw-flows", "enriched-flows"])
                
            self._sub = await self._js.subscribe(
                "enriched-flows", 
                durable="ml_engine_consumer",
                cb=self._message_handler
            )
            logger.info("✅ ML Engine consuming from enriched-flows")
            
        except Exception as e:
            logger.error(f"Failed to start NATS consumer: {e}")

    async def _message_handler(self, msg):
        try:
            flow = json.loads(msg.data.decode())
            
            # Fast Threat Intel check
            threat = None
            src_ip = flow.get("src_ip")
            domain = flow.get("domain")
            
            if src_ip and await self.threat_intel.check_ip(src_ip):
                threat = "MalwareC2_IP"
            elif domain and await self.threat_intel.check_domain(domain):
                threat = "MalwareC2_Domain"
                
            if not threat:
                # ML inference
                feature_vector = self.features.extract(flow)
                scores, labels = self.anomaly_detector.predict(feature_vector)
                
                if labels[0] == -1: # Anomaly
                    pred_threat = self.threat_classifier.predict(feature_vector)[0]
                    if pred_threat != "Normal":
                        threat = pred_threat
            
            if threat:
                # Publish alert
                alert = {
                    "severity": "critical" if "Malware" in threat else "high",
                    "type": threat,
                    "message": f"Detected {threat} from ML inference",
                    "source_ip": src_ip,
                    "device_id": flow.get("device_id"),
                }
                await self._nc.publish("netwatch.alerts", json.dumps(alert).encode())
                logger.info(f"🚨 Published alert: {threat} for {src_ip}")
            
            await msg.ack()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def stop(self):
        """Stop consuming and close connection."""
        if self._sub:
            await self._sub.unsubscribe()
        if self._nc.is_connected:
            await self._nc.close()
