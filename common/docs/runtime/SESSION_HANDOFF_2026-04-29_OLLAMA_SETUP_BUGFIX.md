# SESSION_HANDOFF — 2026-04-29 Ollama 설치 버그 수정

## 1. 이 문서의 목적

Mac mini 실물 하드웨어 설치 중 발생한 Ollama 설정 스크립트 버그 2건을
기록한다. 커밋: `2e13fd7`

---

## 2. 발생 상황

`mac_mini/scripts/configure/30_configure_ollama.sh` 실행 시 아래 오류:

```
[FATAL] Ollama API is not reachable at http://127.0.0.1:11434
Please check Docker logs: docker compose logs ollama
```

`docker ps`에서 `edge_ollama` 컨테이너가 보이고,
`docker compose logs ollama`에서 `listening on [::]:11434` 확인됨.
`curl http://localhost:11434/api/tags` → `{"models":[]}` 정상 응답.

---

## 3. 원인 및 수정

### BUG-1 — API 도달 확인 타이밍 (Race Condition)

**파일:** `mac_mini/scripts/configure/30_configure_ollama.sh`

`docker compose up -d ollama` 직후 Ollama 프로세스가 포트 바인딩을 완료하기
전에 curl을 실행해 FATAL로 종료.

**수정:** 1초 간격 최대 30회 재시도 루프 추가.

```bash
for i in $(seq 1 30); do
    if curl -s -f -o /dev/null "${OLLAMA_HOST}/api/tags"; then
        READY=1; break
    fi
    sleep 1
done
```

### BUG-2 — 모델명 불일치

**파일:** `mac_mini/code/main.py`

| 위치 | 모델명 |
|------|--------|
| `30_configure_ollama.sh` | `llama3.1` (pull 대상) |
| `30_verify_ollama_inference.sh` 기본값 | `llama3.1` |
| `main.py` `OLLAMA_MODEL` 기본값 | `llama3.2` ← 불일치 |

**수정:** `main.py` 기본값을 `llama3.1`로 정렬.
환경변수 `OLLAMA_MODEL`로 오버라이드 가능하므로 `.env`에 명시하면 무관.

---

## 4. 현장 조치 (스크립트 재실행 전 수동 진행)

스크립트 재실행 없이 직접 모델 다운로드:

```bash
docker exec -it edge_ollama ollama pull llama3.1
```

---

## 5. 다음 단계

- `30_configure_ollama.sh` 재실행 가능 (수정 반영됨)
- Ollama 완료 후 Mac mini 설치 다음 단계 계속 진행
