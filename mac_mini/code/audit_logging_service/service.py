"""
Audit Logging Service - MQTT 구독 + 단일 writer DB 기록.

다른 서비스(policy_router, validator 등)는 MQTT topic audit/log/# 에 publish 한다.
이 서비스만 DB 에 직접 쓴다.

MQTT topic 규칙:
  audit/log/routing_event
  audit/log/validator_result
  audit/log/deferral_event
  audit/log/timeout_event
  audit/log/escalation_event
  audit/log/caregiver_action
  audit/log/actuation_ack_event

paho-mqtt 가 없는 환경(테스트 등)을 위해 직접 insert 함수도 제공한다.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .db import AuditDB, DEFAULT_DB_PATH
from .models import (
    ActuationAckEvent,
    CaregiverAction,
    DeferralEvent,
    EscalationEvent,
    RoutingEvent,
    TimeoutEvent,
    ValidatorResult,
)

logger = logging.getLogger(__name__)

# MQTT topic → 이벤트 모델 매핑
_TOPIC_MODEL_MAP = {
    "audit/log/routing_event": RoutingEvent,
    "audit/log/validator_result": ValidatorResult,
    "audit/log/deferral_event": DeferralEvent,
    "audit/log/timeout_event": TimeoutEvent,
    "audit/log/escalation_event": EscalationEvent,
    "audit/log/caregiver_action": CaregiverAction,
    "audit/log/actuation_ack_event": ActuationAckEvent,
}


class AuditLoggingService:
    """
    Audit Logging Service 메인 클래스.
    DB 단일 writer 이며 MQTT 구독을 통해 이벤트를 수신한다.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db = AuditDB(db_path=db_path)
        self._mqtt_client: Optional[Any] = None

    def start(self) -> None:
        """DB 연결 및 스키마 초기화를 수행한다."""
        self.db.connect()
        self.db.init_schema()
        logger.info("AuditLoggingService 시작 완료")

    def stop(self) -> None:
        """DB 연결을 닫는다."""
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        self.db.close()
        logger.info("AuditLoggingService 종료")

    # ── MQTT 연동 ─────────────────────────────────────────────────────────────

    def start_mqtt_subscriber(self, host: str = "localhost", port: int = 1883) -> None:
        """
        MQTT 구독을 시작한다. paho-mqtt 가 설치된 환경에서만 동작한다.
        테스트 환경에서는 직접 insert 함수를 사용한다.
        """
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.warning("paho-mqtt 미설치 - MQTT 구독 없이 직접 insert 모드로 동작")
            return

        client = mqtt.Client()
        client.on_connect = self._on_mqtt_connect
        client.on_message = self._on_mqtt_message
        client.connect(host, port)
        client.loop_start()
        self._mqtt_client = client
        logger.info("MQTT 구독 시작 | broker=%s:%d", host, port)

    def _on_mqtt_connect(self, client: Any, _userdata: Any, _flags: Any, rc: int) -> None:
        """MQTT 연결 완료 시 audit/log/# 를 구독한다."""
        if rc == 0:
            client.subscribe("audit/log/#")
            logger.info("MQTT audit/log/# 구독 완료")
        else:
            logger.error("MQTT 연결 실패 rc=%d", rc)

    def _on_mqtt_message(self, _client: Any, _userdata: Any, message: Any) -> None:
        """MQTT 메시지를 수신하여 적절한 테이블에 insert 한다."""
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            self._dispatch(topic, payload)
        except Exception as exc:
            logger.error("MQTT 메시지 처리 오류 | topic=%s error=%s", topic, exc)

    def _dispatch(self, topic: str, payload: Dict[str, Any]) -> None:
        """topic 에 따라 적절한 insert 함수를 호출한다."""
        model_class = _TOPIC_MODEL_MAP.get(topic)
        if model_class is None:
            logger.warning("알 수 없는 audit topic: %s", topic)
            return

        event = model_class(**payload)

        if topic == "audit/log/routing_event":
            self.db.insert_routing_event(event)
        elif topic == "audit/log/validator_result":
            self.db.insert_validator_result(event)
        elif topic == "audit/log/deferral_event":
            self.db.insert_deferral_event(event)
        elif topic == "audit/log/timeout_event":
            self.db.insert_timeout_event(event)
        elif topic == "audit/log/escalation_event":
            self.db.insert_escalation_event(event)
        elif topic == "audit/log/caregiver_action":
            self.db.insert_caregiver_action(event)
        elif topic == "audit/log/actuation_ack_event":
            self.db.insert_actuation_ack_event(event)

        logger.debug("audit 이벤트 기록 | topic=%s correlation_id=%s",
                     topic, payload.get("audit_correlation_id"))

    # ── 직접 insert (MQTT 없이 사용 가능) ────────────────────────────────────

    def log_routing_event(self, event: RoutingEvent) -> int:
        return self.db.insert_routing_event(event)

    def log_validator_result(self, event: ValidatorResult) -> int:
        return self.db.insert_validator_result(event)

    def log_deferral_event(self, event: DeferralEvent) -> int:
        return self.db.insert_deferral_event(event)

    def log_timeout_event(self, event: TimeoutEvent) -> int:
        return self.db.insert_timeout_event(event)

    def log_escalation_event(self, event: EscalationEvent) -> int:
        return self.db.insert_escalation_event(event)

    def log_caregiver_action(self, event: CaregiverAction) -> int:
        return self.db.insert_caregiver_action(event)

    def log_actuation_ack_event(self, event: ActuationAckEvent) -> int:
        return self.db.insert_actuation_ack_event(event)
