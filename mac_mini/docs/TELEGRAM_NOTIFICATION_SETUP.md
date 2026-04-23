# TELEGRAM_NOTIFICATION_SETUP.md

이 문서는 `mac_mini/scripts/configure/60_configure_notifications.sh`를 **Telegram 모드**로 사용하기 위해 필요한 준비 절차를 자세히 설명한다.

다음 내용을 포함한다.

- Telegram BotFather로 봇 만들기
- 개인 chat 또는 그룹 chat 연결하기
- `chat_id` 확인하기
- `.env`에 값 넣기
- 수동 API 테스트하기
- configure / verify 스크립트와 연결하기
- 자주 발생하는 실수와 보안 주의사항

---

## 1. 무엇이 필요한가

Telegram 알림을 쓰려면 최소 두 값이 필요하다.

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

이 두 값이 준비되지 않으면 `60_configure_notifications.sh`는 Telegram 모드 대신 **mock fallback 모드**로 동작할 수 있다.

---

## 2. BotFather로 Telegram 봇 만들기

### 2.1 BotFather 찾기
1. Telegram 앱을 연다.
2. 검색창에서 `BotFather`를 검색한다.
3. 공식 BotFather와 대화를 시작한다.

### 2.2 새 봇 생성
BotFather 채팅창에서 다음 명령을 보낸다.

```text
/newbot
```

이후 BotFather 안내에 따라 아래 두 값을 정한다.

- 봇 표시 이름
- 봇 username

주의:
- username은 보통 `...bot` 형식으로 끝난다.
- 예: `safe_deferral_alert_bot`

### 2.3 Bot Token 받기
생성이 완료되면 BotFather가 HTTP API token을 발급한다.

예시 형식:

```text
1234567890:AAExampleExampleExampleExampleExample
```

이 값이 `.env`의 `TELEGRAM_BOT_TOKEN`에 들어간다.

---

## 3. 봇과 실제로 대화 시작하기

토큰만 있어서는 메시지가 오지 않을 수 있다. **메시지를 받을 대상 chat에서 먼저 봇과 상호작용**해야 한다.

### 3.1 개인 chat으로 받을 경우
1. Telegram 검색창에서 방금 만든 봇 username을 검색한다.
2. 봇 채팅방에 들어간다.
3. `Start` 버튼을 누르거나 `/start`를 보낸다.

### 3.2 그룹 chat으로 받을 경우
1. Telegram 그룹을 만든다.
2. 해당 그룹에 봇을 초대한다.
3. 그룹에서 최소 한 번 메시지를 보내거나 `/start` 같은 상호작용을 발생시킨다.
4. 필요하면 그룹 설정에서 봇의 메시지 전송 권한을 확인한다.

중요:
- 단순히 봇을 만들기만 해서는 `chat_id`가 바로 안 보일 수 있다.
- 실제 메시지 이벤트가 한 번 발생해야 `getUpdates`로 찾기 쉬워진다.

---

## 4. chat_id 확인 방법

가장 쉬운 방법은 Telegram Bot API의 `getUpdates`를 이용하는 것이다.

### 4.1 먼저 메시지를 하나 보낸다
- 개인 chat이면 봇에게 `/start` 또는 아무 메시지 1개
- 그룹이면 그룹 안에서 메시지 1개

### 4.2 getUpdates 호출
아래 명령을 실행한다.

```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

예:

```bash
curl -s "https://api.telegram.org/bot1234567890:AAExampleExampleExampleExampleExample/getUpdates"
```

### 4.3 응답에서 `chat.id` 찾기
응답 JSON 안에서 `chat` 객체를 찾고, 그 안의 `id` 값을 확인한다.

#### 개인 chat 예시
```json
"chat": {
  "id": 123456789,
  "first_name": "YourName",
  "type": "private"
}
```

#### 그룹 chat 예시
```json
"chat": {
  "id": -1001234567890,
  "title": "Safe Deferral Alerts",
  "type": "supergroup"
}
```

중요:
- 개인 chat ID는 보통 양수다.
- 그룹/supergroup chat ID는 보통 음수이며 `-100...` 형태가 많다.

이 값이 `.env`의 `TELEGRAM_CHAT_ID`에 들어간다.

---

## 5. `.env`에 넣는 방법

`70_write_env_files.sh`를 실행할 때 값을 넣거나, 이후 `~/smarthome_workspace/.env`를 직접 편집해서 다음 두 값을 반영한다.

### 5.1 개인 chat 예시
```bash
TELEGRAM_BOT_TOKEN=1234567890:AAExampleExampleExampleExampleExample
TELEGRAM_CHAT_ID=123456789
```

### 5.2 그룹 chat 예시
```bash
TELEGRAM_BOT_TOKEN=1234567890:AAExampleExampleExampleExampleExample
TELEGRAM_CHAT_ID=-1001234567890
```

주의:
- 앞뒤 공백을 넣지 않는다.
- 줄바꿈이 잘못 들어가지 않게 한다.
- 따옴표는 특별한 경우가 아니면 굳이 넣지 않는다.

---

## 6. Telegram 수동 송신 테스트

스크립트와 별개로 Telegram API가 실제로 동작하는지 확인하려면 아래 명령을 사용한다.

```bash
curl -s -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>" \
  -d "text=Safe Deferral Telegram test message"
```

예:

```bash
curl -s -X POST "https://api.telegram.org/bot1234567890:AAExampleExampleExampleExampleExample/sendMessage" \
  -d "chat_id=123456789" \
  -d "text=Safe Deferral Telegram test message"
```

정상이라면 응답 JSON에 보통 다음이 포함된다.

```json
"ok": true
```

---

## 7. configure / verify 스크립트와 연결하기

### 7.1 configure 실행
`.env` 값이 준비되면 다음을 실행한다.

```bash
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

이 스크립트는 다음처럼 동작한다.

- token/chat ID가 정상 값이면 Telegram mode 시도
- placeholder 또는 미설정이면 mock fallback 사용
- Telegram API test가 실패하면 mock fallback으로 내려갈 수 있음

### 7.2 verify 실행
그 다음 실제 채널이 동작하는지 확인한다.

```bash
bash mac_mini/scripts/verify/60_verify_notifications.sh
```

이 스크립트는 다음 중 하나를 검증한다.

- 실제 Telegram notification channel availability
- 또는 mock fallback channel availability

---

## 8. 자주 발생하는 실수

### 8.1 봇을 만들기만 하고 `/start`를 누르지 않음
증상:
- `getUpdates`에 원하는 chat이 안 나옴
- 메시지가 안 옴

해결:
- 봇과 실제로 대화를 시작한 뒤 다시 `getUpdates` 확인

### 8.2 chat_id를 잘못 입력함
증상:
- Telegram API는 호출되지만 메시지가 안 감
- 다른 chat으로 가거나 실패함

해결:
- `getUpdates`에서 실제 `chat.id` 값을 다시 확인

### 8.3 그룹에 봇을 초대만 하고 메시지를 보내지 않음
증상:
- 그룹 chat ID를 못 찾음

해결:
- 그룹에서 최소 한 번 메시지를 보내거나 상호작용을 발생시킨 뒤 `getUpdates` 재확인

### 8.4 token 값에 공백/줄바꿈이 들어감
증상:
- Telegram API 인증 실패

해결:
- `.env` 값에 공백, 복사 실수, 줄바꿈이 없는지 확인

### 8.5 Telegram API 실패 후 mock fallback으로 내려감
증상:
- `60_configure_notifications.sh`는 통과했지만 실제 Telegram 발송이 안 됨

해결:
- `60_configure_notifications.sh` 출력과 `60_verify_notifications.sh` 결과를 같이 확인
- 먼저 `curl sendMessage`로 수동 API 테스트를 해본다

---

## 9. 보안 주의사항

- `TELEGRAM_BOT_TOKEN`은 비밀값으로 취급한다.
- 스크린샷, 논문, 공개 저장소, 커밋 메시지에 토큰을 남기지 않는다.
- 토큰이 유출되면 BotFather에서 revoke 또는 재발급 절차를 진행한다.
- `.env`는 deployment-local 파일이며 canonical policy truth가 아니다.

---

## 10. 권장 최소 절차 요약

가장 짧게 정리하면 아래 순서다.

1. BotFather에서 봇 만들기
2. 봇과 `/start` 하기
3. `getUpdates`로 `chat_id` 확인하기
4. `.env`에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 넣기
5. `bash mac_mini/scripts/configure/60_configure_notifications.sh`
6. `bash mac_mini/scripts/verify/60_verify_notifications.sh`

---

## 11. 바로 복붙용 명령 예시

### getUpdates 확인
```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

### 수동 송신 테스트
```bash
curl -s -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>" \
  -d "text=Safe Deferral Telegram test message"
```

### configure / verify
```bash
bash mac_mini/scripts/configure/60_configure_notifications.sh
bash mac_mini/scripts/verify/60_verify_notifications.sh
```
