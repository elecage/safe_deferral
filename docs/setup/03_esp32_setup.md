# ESP32 물리 노드 펌웨어 빌드·플래시 / ESP32 Physical Node Firmware Build & Flash

---

## 1. 개요 / Overview

**한국어**  
ESP32 물리 노드는 `safe_deferral`의 bounded input/output 계층입니다. 각 노드는 ESP-IDF(Espressif IoT Development Framework) C 펌웨어로 구현되며, MQTT를 통해 Mac mini와 통신합니다. 정책 라우팅, 검증, 보호자 승인 권한은 갖지 않습니다.

**English**  
ESP32 physical nodes form the bounded input/output layer of `safe_deferral`. Each node is implemented as an ESP-IDF C firmware project and communicates with the Mac mini over MQTT. Nodes have no policy routing, validation, or caregiver approval authority.

---

## 2. 노드 목록 / Node List

| 디렉토리 / Directory | 노드 / Node | 설명 / Description |
|---|---|---|
| `pn01_button_input` | PN-01 | 물리 버튼 입력 / Physical button input |
| `pn02_lighting_control` | PN-02 | 조명 제어 (living room / bedroom) / Lighting control |
| `pn03_env_context` | PN-03 | 환경 컨텍스트 (온도·조도·재실) / Environmental context |
| `pn04_doorbell` | PN-04 | 도어벨 방문자 컨텍스트 / Doorbell visitor context |
| `pn05_gas_smoke_fire` | PN-05 | 가스·연기·화재 비상 증거 / Gas/smoke/fire emergency evidence |
| `pn06_fall_detection` | PN-06 | 낙상 감지 (IMU 2단계) / Fall detection (IMU two-phase) |
| `pn07_warning_output` | PN-07 | 부저·LED·TTS 경고 출력 / Buzzer/LED/TTS warning output |
| `pn08_doorlock_interface` | PN-08 | 거버닝된 도어락 인터페이스 / Governed doorlock interface |

---

## 3. 사전 요구사항 / Prerequisites

**한국어**

| 구성요소 | 버전 | 설치 방법 |
|---|---|---|
| ESP-IDF | v5.1 이상 | [공식 설치 가이드](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/) |
| CMake | 3.16 이상 | ESP-IDF 설치 시 포함 |
| Python | 3.8 이상 | ESP-IDF 내부에서 사용 |
| USB 드라이버 | CP210x 또는 CH340 | 보드에 따라 다름 |

macOS에서 ESP-IDF 설치:
```bash
mkdir -p ~/esp && cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.1
./install.sh esp32
source ./export.sh
```

**English**

| Component | Version | Installation |
|---|---|---|
| ESP-IDF | v5.1 or later | [Official guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/) |
| CMake | 3.16+ | Included with ESP-IDF |
| Python | 3.8+ | Used internally by ESP-IDF |
| USB driver | CP210x or CH340 | Depends on your board |

Install ESP-IDF on macOS:
```bash
mkdir -p ~/esp && cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.1
./install.sh esp32
source ./export.sh
```

---

## 4. MQTT 브로커 URI 설정 / MQTT Broker URI Configuration

**한국어**  
각 노드는 `CONFIG_SD_MQTT_BROKER_URI`를 `idf.py menuconfig`로 설정합니다.

```bash
cd esp32/code/<node_directory>

# ESP-IDF 환경 활성화
source ~/esp/esp-idf/export.sh

# menuconfig 실행
idf.py menuconfig
# → Component config → safe_deferral → MQTT Broker URI
# 예: mqtt://192.168.1.100:1883
```

또는 `sdkconfig.defaults` 파일로 사전 설정:
```
# esp32/code/<node>/sdkconfig.defaults
CONFIG_SD_MQTT_BROKER_URI="mqtt://192.168.1.100:1883"
```

**English**  
Each node reads `CONFIG_SD_MQTT_BROKER_URI` set via `idf.py menuconfig`.

```bash
cd esp32/code/<node_directory>

# Activate ESP-IDF environment
source ~/esp/esp-idf/export.sh

# Open menuconfig
idf.py menuconfig
# → Component config → safe_deferral → MQTT Broker URI
# e.g. mqtt://192.168.1.100:1883
```

Or pre-configure with `sdkconfig.defaults`:
```
# esp32/code/<node>/sdkconfig.defaults
CONFIG_SD_MQTT_BROKER_URI="mqtt://192.168.1.100:1883"
```

---

## 5. 빌드 및 플래시 / Build and Flash

**한국어**

```bash
# ESP-IDF 환경 활성화 (한 번만)
source ~/esp/esp-idf/export.sh

# 노드 디렉토리로 이동 (예: PN-01)
cd /path/to/safe_deferral_claude/esp32/code/pn01_button_input

# 빌드
idf.py build

# 플래시 (포트는 보드에 따라 다름)
idf.py -p /dev/cu.usbserial-0001 flash

# 시리얼 모니터
idf.py -p /dev/cu.usbserial-0001 monitor
```

Linux에서 포트 예시: `/dev/ttyUSB0`, `/dev/ttyACM0`

**English**

```bash
# Activate ESP-IDF environment (once per terminal)
source ~/esp/esp-idf/export.sh

# Navigate to node directory (e.g. PN-01)
cd /path/to/safe_deferral_claude/esp32/code/pn01_button_input

# Build
idf.py build

# Flash (port depends on your board)
idf.py -p /dev/cu.usbserial-0001 flash

# Serial monitor
idf.py -p /dev/cu.usbserial-0001 monitor
```

Linux port examples: `/dev/ttyUSB0`, `/dev/ttyACM0`

---

## 6. GPIO 핀 매핑 (ESP32-C3 Super Mini) / GPIO Pin Mapping

**한국어**

ESP32-C3 Super Mini 핀 제약:
- `GPIO18/19`: USB D-/D+ — 출력으로 사용 불가
- `GPIO20/21`: UART0 RX/TX — 플래싱 전용, 충돌 금지
- `GPIO9`: 내장 Boot 버튼 (PN-01에서 활용)
- `GPIO2/8`: 스트래핑 핀 — 사용 가능하나 boot 모드에 영향 가능
- ADC 가능 핀: `GPIO0~GPIO4` (Wi-Fi 활성 시 ADC2 사용 불가)
- LEDC: **Low-speed mode만 지원**

| 노드 | GPIO | 역할 |
|---|---|---|
| PN-01 | **GPIO_9** | 내장 Boot 버튼 (Active-LOW, 내부 풀업) |
| PN-02 | **GPIO_4** | living_room_light 릴레이 |
| PN-02 | **GPIO_5** | bedroom_light 릴레이 |
| PN-04 | **GPIO_3** | 도어벨 버튼 입력 |
| PN-05 | **GPIO_0** | 가스 센서 ADC (MQ-2, ADC1_CH0) |
| PN-05 | **GPIO_1** | 연기 센서 ADC (ADC1_CH1) |
| PN-06 | **GPIO_8** | IMU I2C SDA (MPU-6050) |
| PN-06 | **GPIO_10** | IMU I2C SCL |
| PN-07 | **GPIO_6** | 부저 (PWM LEDC CH0, Low-speed) |
| PN-07 | **GPIO_7** | 상태 LED |
| PN-07 | **GPIO_10** | TTS 모듈 UART1 TX (GPIO matrix 재매핑) |
| PN-08 | **GPIO_4** | 도어락 릴레이 (HIGH=잠금) |
| PN-08 | **GPIO_5** | 도어락 상태 LED |

> **주의**: PN-06(I2C SCL)과 PN-07(TTS TX)이 GPIO_10을 공유합니다. 별도 보드에서 사용하거나, PN-07 TTS TX를 GPIO_0으로 변경하세요.

핀 번호는 각 `.c` 소스 파일 상단 `#define` 에서 변경할 수 있습니다.

**English**

ESP32-C3 Super Mini pin constraints:
- `GPIO18/19`: USB D-/D+ — cannot be used as outputs
- `GPIO20/21`: UART0 RX/TX — reserved for flashing, do not conflict
- `GPIO9`: Built-in Boot button (used by PN-01)
- `GPIO2/8`: Strapping pins — usable but may affect boot mode
- ADC-capable: `GPIO0~GPIO4` (ADC2 unavailable when Wi-Fi is active)
- LEDC: **Low-speed mode only** (no high-speed mode on C3)

| Node | GPIO | Role |
|---|---|---|
| PN-01 | **GPIO_9** | Built-in Boot button (active-LOW, internal pull-up) |
| PN-02 | **GPIO_4** | living_room_light relay |
| PN-02 | **GPIO_5** | bedroom_light relay |
| PN-04 | **GPIO_3** | Doorbell button input |
| PN-05 | **GPIO_0** | Gas sensor ADC (MQ-2, ADC1_CH0) |
| PN-05 | **GPIO_1** | Smoke sensor ADC (ADC1_CH1) |
| PN-06 | **GPIO_8** | IMU I2C SDA (MPU-6050) |
| PN-06 | **GPIO_10** | IMU I2C SCL |
| PN-07 | **GPIO_6** | Buzzer (PWM LEDC CH0, low-speed) |
| PN-07 | **GPIO_7** | Status LED |
| PN-07 | **GPIO_10** | TTS module UART1 TX (remapped via GPIO matrix) |
| PN-08 | **GPIO_4** | Doorlock relay (HIGH=locked) |
| PN-08 | **GPIO_5** | Doorlock status LED |

> **Note**: PN-06 (I2C SCL) and PN-07 (TTS TX) share GPIO_10. Use them on separate boards or change PN-07 TTS TX to GPIO_0.

Pin numbers can be changed in the `#define` block at the top of each `.c` source file.

---

## 7. 동작 확인 / Verification

**한국어**

시리얼 모니터에서 아래 로그가 출력되면 정상입니다:

```
I (xxx) pn01_button: PN-01 Button Input Node starting, source_id=esp32.button_node_01
I (xxx) pn01_button: GPIO 0 configured for button input
I (xxx) pn01_button: MQTT client started, broker=mqtt://192.168.1.100:1883
I (xxx) pn01_button: MQTT connected
I (xxx) pn01_button: PN-01 ready — press GPIO0 to publish context input
```

MQTT 구독으로 확인 (Mac mini 또는 PC에서):
```bash
mosquitto_sub -h 192.168.1.100 -t "safe_deferral/context/input" -v
```
버튼을 누르면 JSON 페이로드가 출력됩니다.

**English**

The following log output in the serial monitor indicates normal operation:

```
I (xxx) pn01_button: PN-01 Button Input Node starting, source_id=esp32.button_node_01
I (xxx) pn01_button: GPIO 0 configured for button input
I (xxx) pn01_button: MQTT client started, broker=mqtt://192.168.1.100:1883
I (xxx) pn01_button: MQTT connected
I (xxx) pn01_button: PN-01 ready — press GPIO0 to publish context input
```

Verify with MQTT subscription (from Mac mini or PC):
```bash
mosquitto_sub -h 192.168.1.100 -t "safe_deferral/context/input" -v
```
Pressing the button should produce a JSON payload output.

---

## 8. 안전 기본값 / Safe Defaults

**한국어**  
모든 노드는 재연결/재부팅 시 보수적인 기본 상태로 복귀합니다:
- PN-02: 모든 조명 OFF
- PN-08: 도어락 잠금 체결 (Lock ENGAGED)
- PN-05/06: 알람 상태 초기화

**English**  
All nodes return to a conservative safe state on reconnect/reboot:
- PN-02: All lights OFF
- PN-08: Doorlock ENGAGED (locked)
- PN-05/06: Alert state reset
