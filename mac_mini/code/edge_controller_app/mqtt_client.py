"""
엣지 컨트롤러 MQTT 클라이언트.

MQTT 브로커와의 pub/sub를 관리한다.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Callable, Optional

from policy_router.models import PolicyRouterInput

logger = logging.getLogger(__name__)

# MQTT 의존성 선택적 import
try:
    import paho.mqtt.client as mqtt

    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    logger.warning("paho-mqtt 미설치 - MQTT 기능 비활성화")


class MQTTClient:
    """
    MQTT 클라이언트 wrapper.

    입력을 수신하고 결과를 퍼블리시한다.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 1883,
        on_message_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        초기화.

        Args:
            host: MQTT 브로커 호스트
            port: MQTT 브로커 포트
            on_message_callback: 메시지 수신 콜백 함수
        """
        if not HAS_MQTT:
            logger.warning("MQTT 클라이언트 초기화 불가 - paho-mqtt 미설치")
            self.client = None
            return

        self.host = host
        self.port = port
        self.on_message_callback = on_message_callback
        self.client = mqtt.Client()

        # 콜백 등록
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def connect(self) -> None:
        """
        MQTT 브로커에 연결.

        Raises:
            RuntimeError: MQTT 클라이언트 초기화 실패
        """
        if not self.client:
            raise RuntimeError("MQTT 클라이언트 초기화되지 않음")

        try:
            logger.info("MQTT 브로커 연결 시도 | host=%s port=%d", self.host, self.port)
            self.client.connect(self.host, self.port, keepalive=60)
            logger.info("MQTT 브로커 연결 성공")
        except Exception as exc:
            logger.error(
                "MQTT 브로커 연결 실패 | host=%s port=%d error=%s",
                self.host,
                self.port,
                exc,
                exc_info=True,
            )
            raise

    def disconnect(self) -> None:
        """MQTT 브로커 연결 해제."""
        if self.client:
            logger.info("MQTT 브로커 연결 해제")
            self.client.disconnect()

    def start(self) -> None:
        """MQTT 루프 시작."""
        if self.client:
            self.client.loop_start()
            logger.info("MQTT 루프 시작")

    def stop(self) -> None:
        """MQTT 루프 종료."""
        if self.client:
            self.client.loop_stop()
            logger.info("MQTT 루프 종료")

    def publish(self, topic: str, payload: str) -> None:
        """
        MQTT 토픽에 메시지 퍼블리시.

        Args:
            topic: MQTT 토픽
            payload: JSON 문자열 페이로드
        """
        if not self.client:
            logger.warning("MQTT 퍼블리시 불가 - 클라이언트 미초기화 | topic=%s", topic)
            return

        try:
            result = self.client.publish(topic, payload, qos=1)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(
                    "MQTT 퍼블리시 실패 | topic=%s rc=%d", topic, result.rc
                )
            else:
                logger.debug("MQTT 퍼블리시 성공 | topic=%s", topic)
        except Exception as exc:
            logger.error(
                "MQTT 퍼블리시 예외 | topic=%s error=%s",
                topic,
                exc,
                exc_info=True,
            )

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT 연결 콜백."""
        if rc == 0:
            logger.info("MQTT 연결 성공")
            # 입력 토픽 구독
            client.subscribe("smarthome/context/raw", qos=1)
            logger.info("MQTT 토픽 구독 | topic=smarthome/context/raw")
        else:
            logger.error("MQTT 연결 실패 | rc=%d", rc)

    def _on_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 콜백."""
        if rc != 0:
            logger.warning("MQTT 예상치 못한 연결 해제 | rc=%d", rc)
        else:
            logger.info("MQTT 연결 정상 해제")

    def _on_message(self, client, userdata, msg):
        """
        MQTT 메시지 수신 콜백.

        Args:
            client: MQTT 클라이언트
            userdata: 사용자 데이터
            msg: 수신 메시지
        """
        try:
            topic = msg.topic
            payload_str = msg.payload.decode("utf-8")
            logger.debug("MQTT 메시지 수신 | topic=%s", topic)

            if self.on_message_callback:
                self.on_message_callback(payload_str)

        except Exception as exc:
            logger.error(
                "MQTT 메시지 처리 오류 | topic=%s error=%s",
                msg.topic,
                exc,
                exc_info=True,
            )


def create_mqtt_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    on_message_callback: Optional[Callable[[str], None]] = None,
) -> Optional[MQTTClient]:
    """
    MQTT 클라이언트 생성.

    환경변수에서 호스트/포트를 읽고, MQTT가 설치되어 있으면 클라이언트를 생성한다.

    Args:
        host: MQTT 호스트 (기본: 환경변수 MQTT_HOST 또는 127.0.0.1)
        port: MQTT 포트 (기본: 환경변수 MQTT_PORT 또는 1883)
        on_message_callback: 메시지 콜백

    Returns:
        MQTTClient 인스턴스 또는 None (MQTT 미설치)
    """
    if not HAS_MQTT:
        logger.warning("MQTT 클라이언트 미생성 - paho-mqtt 미설치")
        return None

    host = host or os.environ.get("MQTT_HOST", "127.0.0.1")
    port = port or int(os.environ.get("MQTT_PORT", "1883"))

    client = MQTTClient(
        host=host, port=port, on_message_callback=on_message_callback
    )
    return client
