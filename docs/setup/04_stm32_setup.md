# STM32 타이밍 측정 노드 설치 및 설정 / STM32 Timing Measurement Node Setup

---

## 1. 개요 / Overview

**한국어**  
STM32 Nucleo-H723ZG는 out-of-band 타이밍 캡처 노드입니다. 실험 중 물리 에지(trigger/observe/actuate) 타임스탬프를 µs 단위로 수집하여 UART3(USB 가상 COM)으로 CSV 형태로 내보냅니다. 운영 제어 경로에 속하지 않으며 정책·액추에이터 권한이 없습니다.

**English**  
The STM32 Nucleo-H723ZG is an out-of-band timing capture node. It collects physical edge (trigger/observe/actuate) timestamps at µs resolution during experiments and exports them as CSV rows over UART3 (USB virtual COM). It is not part of the operational control path and has no policy or actuator authority.

---

## 2. 사전 요구사항 / Prerequisites

**한국어**

| 구성요소 | 버전 | 설치 방법 |
|---|---|---|
| ARM GCC Toolchain | 12.x 이상 | `brew install --cask gcc-arm-embedded` (macOS) 또는 [공식 다운로드](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads) |
| CMake | 3.16 이상 | `brew install cmake` |
| STM32CubeH7 | V1.11 이상 | [ST 공식 사이트](https://www.st.com/en/embedded-software/stm32cubeh7.html) 다운로드 |
| STM32CubeProgrammer | 2.x | [ST 공식 사이트](https://www.st.com/en/development-tools/stm32cubeprog.html) |
| OpenOCD | 0.12 이상 (선택) | `brew install openocd` |
| 시리얼 터미널 | — | macOS: `screen`, Linux: `minicom`, Windows: PuTTY |

**English**

| Component | Version | Installation |
|---|---|---|
| ARM GCC Toolchain | 12.x+ | `brew install --cask gcc-arm-embedded` (macOS) or [official download](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads) |
| CMake | 3.16+ | `brew install cmake` |
| STM32CubeH7 | V1.11+ | Download from [ST website](https://www.st.com/en/embedded-software/stm32cubeh7.html) |
| STM32CubeProgrammer | 2.x | Download from [ST website](https://www.st.com/en/development-tools/stm32cubeprog.html) |
| OpenOCD | 0.12+ (optional) | `brew install openocd` |
| Serial terminal | — | macOS: `screen`, Linux: `minicom`, Windows: PuTTY |

---

## 3. STM32CubeH7 HAL 드라이버 준비 / Preparing STM32CubeH7 HAL Drivers

**한국어**  
CMake 빌드는 HAL 드라이버를 저장소에 포함하지 않습니다. 별도 경로에서 참조합니다.

```bash
# STM32CubeH7 경로 설정 (다운로드 후 압축 해제 위치)
export STM32CUBE_H7=~/STM32Cube/Repository/STM32Cube_FW_H7_V1.11.2

# 스타트업 파일과 링커 스크립트를 Drivers 폴더로 복사
cd /path/to/safe_deferral_claude/integration/measurement/stm32

cp $STM32CUBE_H7/Drivers/CMSIS/Device/ST/STM32H7xx/Source/Templates/gcc/startup_stm32h723zgtx.s \
   Drivers/

cp $STM32CUBE_H7/Drivers/CMSIS/Device/ST/STM32H7xx/Source/Templates/system_stm32h7xx.c \
   Drivers/

# 링커 스크립트는 STM32CubeIDE 예제 프로젝트에서 복사하거나
# ST GitHub의 Nucleo-H723ZG 예제에서 가져옵니다
# 파일명: STM32H723ZGTx_FLASH.ld → Drivers/ 에 배치
```

**English**  
The CMake build references HAL drivers from a separate path rather than including them in the repository.

```bash
# Set path to STM32CubeH7 (after download and extraction)
export STM32CUBE_H7=~/STM32Cube/Repository/STM32Cube_FW_H7_V1.11.2

# Copy startup file and linker script to the Drivers folder
cd /path/to/safe_deferral_claude/integration/measurement/stm32

cp $STM32CUBE_H7/Drivers/CMSIS/Device/ST/STM32H7xx/Source/Templates/gcc/startup_stm32h723zgtx.s \
   Drivers/

cp $STM32CUBE_H7/Drivers/CMSIS/Device/ST/STM32H7xx/Source/Templates/system_stm32h7xx.c \
   Drivers/

# The linker script should be copied from a STM32CubeIDE example project
# or from the Nucleo-H723ZG example on ST GitHub
# File name: STM32H723ZGTx_FLASH.ld → place in Drivers/
```

---

## 4. 빌드 / Build

**한국어**

```bash
cd /path/to/safe_deferral_claude/integration/measurement/stm32

# CMake 툴체인 파일 생성 (최초 1회)
cat > cmake/arm-none-eabi.cmake << 'EOF'
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
EOF

mkdir -p build && cd build
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE=../cmake/arm-none-eabi.cmake \
    -DSTM32CUBE_H7=$STM32CUBE_H7 \
    -DCMAKE_BUILD_TYPE=Release

make -j4
# 결과물: build/sd_measure.elf, build/sd_measure.hex, build/sd_measure.bin
```

**English**

```bash
cd /path/to/safe_deferral_claude/integration/measurement/stm32

# Create CMake toolchain file (first time only)
cat > cmake/arm-none-eabi.cmake << 'EOF'
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
EOF

mkdir -p build && cd build
cmake .. \
    -DCMAKE_TOOLCHAIN_FILE=../cmake/arm-none-eabi.cmake \
    -DSTM32CUBE_H7=$STM32CUBE_H7 \
    -DCMAKE_BUILD_TYPE=Release

make -j4
# Output: build/sd_measure.elf, build/sd_measure.hex, build/sd_measure.bin
```

---

## 5. 플래시 / Flash

**한국어**

**방법 A — STM32CubeProgrammer (GUI)**  
1. Nucleo-H723ZG를 USB로 연결합니다.  
2. STM32CubeProgrammer를 실행합니다.  
3. ST-LINK 인터페이스를 선택하고 Connect를 클릭합니다.  
4. `sd_measure.hex`를 로드하고 Program & Verify를 클릭합니다.

**방법 B — STM32CubeProgrammer CLI**
```bash
STM32_Programmer_CLI \
    -c port=SWD \
    -d build/sd_measure.hex \
    -v \
    -rst
```

**방법 C — OpenOCD**
```bash
openocd \
    -f interface/stlink.cfg \
    -f target/stm32h7x.cfg \
    -c "program build/sd_measure.elf verify reset exit"
```

**English**

**Method A — STM32CubeProgrammer (GUI)**  
1. Connect the Nucleo-H723ZG via USB.  
2. Open STM32CubeProgrammer.  
3. Select ST-LINK interface and click Connect.  
4. Load `sd_measure.hex` and click Program & Verify.

**Method B — STM32CubeProgrammer CLI**
```bash
STM32_Programmer_CLI \
    -c port=SWD \
    -d build/sd_measure.hex \
    -v \
    -rst
```

**Method C — OpenOCD**
```bash
openocd \
    -f interface/stlink.cfg \
    -f target/stm32h7x.cfg \
    -c "program build/sd_measure.elf verify reset exit"
```

---

## 6. 시리얼 터미널 연결 / Serial Terminal Connection

**한국어**

Nucleo-H723ZG는 USB 연결 시 가상 COM 포트(UART3, PD8/PD9)로 UART 출력을 제공합니다.

```bash
# macOS
screen /dev/cu.usbmodem* 115200

# Linux
minicom -D /dev/ttyACM0 -b 115200

# 연결 후 정상 부팅 시 출력 예:
# sd_measure boot
# node_id=stm32_time_probe_01 fw=1.0.0
# SELFTEST_FW_VERSION: 1.0.0 PASS
# SELFTEST_TIMER: PASS
# SELFTEST_CAPTURE_CH_A: PASS
# ...
# SELFTEST_RESULT: READY
```

**English**

The Nucleo-H723ZG provides UART output over a virtual COM port (UART3, PD8/PD9) when connected via USB.

```bash
# macOS
screen /dev/cu.usbmodem* 115200

# Linux
minicom -D /dev/ttyACM0 -b 115200

# Expected output after successful boot:
# sd_measure boot
# node_id=stm32_time_probe_01 fw=1.0.0
# SELFTEST_FW_VERSION: 1.0.0 PASS
# SELFTEST_TIMER: PASS
# SELFTEST_CAPTURE_CH_A: PASS
# ...
# SELFTEST_RESULT: READY
```

---

## 7. 측정 세션 운영 / Running a Measurement Session

**한국어**

```bash
# 시리얼 터미널에서 커맨드 전송

# 세션 시작 (실험 ID 포함)
echo "SESSION_START EXP_CLASSWISE_LATENCY_CLASS1" > /dev/cu.usbmodem*

# 실험 실행 (RPi 실험 러너에서 별도 수행)

# 세션 종료
echo "SESSION_STOP" > /dev/cu.usbmodem*

# 상태 확인
echo "STATUS" > /dev/cu.usbmodem*
```

출력 CSV 행 형식:
```
HEADER: type,session_id,seq,channel,raw_ticks,overflow_count,abs_us,quality
DATA,1,0,CH_A,1234567,0,1234567,0
DATA,1,1,CH_B,1289034,0,1289034,0
DATA,1,2,CH_C,1312488,0,1312488,0
META,1,EXP_CLASSWISE_LATENCY_CLASS1,1000000,1500000,3
```

**English**

```bash
# Send commands from the serial terminal

# Start session (with experiment ID)
echo "SESSION_START EXP_CLASSWISE_LATENCY_CLASS1" > /dev/cu.usbmodem*

# Run experiment (via RPi experiment runner separately)

# Stop session
echo "SESSION_STOP" > /dev/cu.usbmodem*

# Check status
echo "STATUS" > /dev/cu.usbmodem*
```

Output CSV row format:
```
HEADER: type,session_id,seq,channel,raw_ticks,overflow_count,abs_us,quality
DATA,1,0,CH_A,1234567,0,1234567,0
DATA,1,1,CH_B,1289034,0,1289034,0
DATA,1,2,CH_C,1312488,0,1312488,0
META,1,EXP_CLASSWISE_LATENCY_CLASS1,1000000,1500000,3
```

---

## 8. 캡처 채널 배선 / Capture Channel Wiring

**한국어**

| 채널 | 핀 | 역할 | 에지 소스 예시 |
|---|---|---|---|
| CH_A | PA0 (TIM2_CH1) | 트리거 소스 에지 | ESP32 버튼 노드 GPIO 출력 |
| CH_B | PA1 (TIM2_CH2) | 허브 관찰 에지 | Mac mini GPIO 또는 UART 신호 |
| CH_C | PA2 (TIM2_CH3) | 액추에이터 ACK 에지 | ESP32 조명 노드 ACK 출력 |
| CH_D | PA3 (TIM2_CH4) | 예비 | — |

> **주의**: 측정 배선은 운영 제어 경로와 분리되어야 합니다. 캡처 입력이 액추에이터 명령을 주입하면 안 됩니다.

**English**

| Channel | Pin | Role | Example Edge Source |
|---|---|---|---|
| CH_A | PA0 (TIM2_CH1) | Trigger source edge | ESP32 button node GPIO output |
| CH_B | PA1 (TIM2_CH2) | Hub observable edge | Mac mini GPIO or UART signal |
| CH_C | PA2 (TIM2_CH3) | Actuator ACK edge | ESP32 lighting node ACK output |
| CH_D | PA3 (TIM2_CH4) | Spare | — |

> **Note**: Measurement wiring must be separated from the operational control path. Capture inputs must never inject actuator commands.

---

## 9. 검증 체크리스트 / Validation Checklist

**한국어**  
전체 체크리스트는 `integration/measurement/stm32/VALIDATION_CHECKLIST.md` 를 참조하세요.

핵심 항목:
- [ ] 부팅 후 LD1(녹색) LED 점등
- [ ] 시리얼에서 `SELFTEST_RESULT: READY` 출력
- [ ] 하트비트 JSON 5초마다 수신
- [ ] PA0에 신호 인가 시 `DATA,...,CH_A,...` 행 출력
- [ ] MQTT 트래픽 없음 (운영 사이드 이펙트 없음)

**English**  
See `integration/measurement/stm32/VALIDATION_CHECKLIST.md` for the full checklist.

Key items:
- [ ] LD1 (green) LED on after boot
- [ ] `SELFTEST_RESULT: READY` in serial output
- [ ] Heartbeat JSON received every 5 seconds
- [ ] `DATA,...,CH_A,...` row when signal applied to PA0
- [ ] No MQTT traffic (no operational side effects)

---

## 10. RPi 데이터 수집 / Data Collection to RPi

**한국어**

```bash
# RPi에서 STM32 시리얼 로그를 파일로 저장
# (RPi가 USB로 Nucleo에 연결된 경우)
cat /dev/ttyACM0 > /tmp/session_raw.csv &

# 세션 종료 후 결과를 RPi result store로 이동
cp /tmp/session_raw.csv \
    /path/to/safe_deferral_claude/integration/measurement/results/
```

**English**

```bash
# Save STM32 serial log to file from RPi
# (when RPi is connected to Nucleo via USB)
cat /dev/ttyACM0 > /tmp/session_raw.csv &

# After session stop, move results to RPi result store
cp /tmp/session_raw.csv \
    /path/to/safe_deferral_claude/integration/measurement/results/
```
