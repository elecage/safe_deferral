# Edge Controller App Docker Image
#
# 정책 기반 결정론적 라우팅 및 검증 오케스트레이터
# MQTT 입력을 수신하고 폐쇄 루프 감사를 수행한다.

FROM python:3.9-slim

WORKDIR /app

# 타임존 설정
ENV TZ=Asia/Seoul

# 코드 복사
COPY . /app/code/
COPY common /app/common/

# 의존성 설치
RUN cd /app/code && pip install --no-cache-dir -r requirements.txt

# Python path 설정 (mac_mini/code를 포함)
ENV PYTHONPATH=/app/code:$PYTHONPATH

# 헬스 체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 진입점: edge_controller_app FastAPI 서비스 실행
CMD ["uvicorn", "edge_controller_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
