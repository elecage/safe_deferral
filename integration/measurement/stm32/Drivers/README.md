# Drivers

이 디렉토리에는 STM32CubeH7 CMSIS/HAL 드라이버 파일을 **복사하지 않는다**.

빌드 시 `STM32CUBE_H7` 환경변수 또는 CMake 변수로 STM32CubeH7 설치 경로를 지정한다.

```bash
export STM32CUBE_H7=~/STM32Cube/Repository/STM32Cube_FW_H7_V1.11.2
cmake -B build -DSTM32CUBE_H7=$STM32CUBE_H7 \
      -DCMAKE_TOOLCHAIN_FILE=../cmake/arm-none-eabi.cmake ..
```

## 필요 파일 (빌드 전 복사 또는 심볼릭 링크)

아래 파일은 STM32CubeH7에서 이 디렉토리로 복사해서 사용한다:

- `startup_stm32h723zgtx.s`
  - 위치: `STM32Cube_FW_H7_V1.11.2/Drivers/CMSIS/Device/ST/STM32H7xx/Source/Templates/gcc/startup_stm32h723zgtx.s`
- `system_stm32h7xx.c`
  - 위치: `STM32Cube_FW_H7_V1.11.2/Drivers/CMSIS/Device/ST/STM32H7xx/Source/Templates/system_stm32h7xx.c`
- `STM32H723ZGTx_FLASH.ld`
  - 위치: STM32CubeIDE project generation 결과물 또는 Nucleo-H723ZG 예제 프로젝트에서 복사

## STM32CubeIDE 사용 시

STM32CubeIDE로 새 프로젝트 생성 후 이 소스 파일들을 추가하면
startup/linker/HAL 설정이 자동으로 포함된다.
