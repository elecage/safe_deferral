# Edge Controller App Docker Image
#
# 정책 기반 결정론적 라우팅 및 검증 오케스트레이터
# MQTT 입력을 수신하고 폐쇄 루프 감사를 수행한다.

FROM python:3.9-slim

WORKDIR /app

# 타임존 설정
ENV TZ=Asia/Seoul

# 저장소 루트 전체를 build context로 복사
COPY . /app/repo/

# 의존성 설치 (repo root 기준)
RUN pip install --no-cache-dir -r /app/repo/mac_mini/code/requirements.txt

# Python path 설정 (repo root와 mac_mini/code를 모두 포함)
ENV PYTHONPATH=/app/repo:/app/repo/mac_mini/code:$PYTHONPATH

# 실행 작업 디렉터리
WORKDIR /app/repo/mac_mini/code

# 헬스 체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 진입점: edge_controller_app FastAPI 서비스 실행
CMD ["uvicorn", "edge_controller_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
