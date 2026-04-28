cmake_minimum_required(VERSION 3.16)

# STM32 cross-compilation toolchain must be set before project()
# Usage: cmake -DCMAKE_TOOLCHAIN_FILE=arm-none-eabi.cmake ..
# Or via STM32CubeIDE which generates its own Makefile/Eclipse project.

project(sd_measure C ASM)

set(CMAKE_C_STANDARD 11)

# STM32H723ZG target
set(MCU_FLAGS "-mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard")
set(CMAKE_C_FLAGS "${MCU_FLAGS} -Wall -fdata-sections -ffunction-sections")
set(CMAKE_EXE_LINKER_FLAGS
    "${MCU_FLAGS} -specs=nano.specs -T${CMAKE_SOURCE_DIR}/Drivers/STM32H723ZGTx_FLASH.ld \
     -lc -lm -lnosys -Wl,--gc-sections -Wl,-Map=sd_measure.map")

# HAL driver path — set via -DSTM32CUBE_H7=<path> or environment variable
if(NOT DEFINED STM32CUBE_H7)
    set(STM32CUBE_H7 "$ENV{HOME}/STM32Cube/Repository/STM32Cube_FW_H7_V1.11.2")
endif()

set(HAL_SRC_DIR "${STM32CUBE_H7}/Drivers/STM32H7xx_HAL_Driver/Src")
set(CMSIS_DIR   "${STM32CUBE_H7}/Drivers/CMSIS")

add_definitions(
    -DUSE_HAL_DRIVER
    -DSTM32H723xx
)

include_directories(
    Core/Inc
    Modules/capture
    Modules/sync
    Modules/export
    Modules/status
    Modules/validation
    ${STM32CUBE_H7}/Drivers/STM32H7xx_HAL_Driver/Inc
    ${CMSIS_DIR}/Device/ST/STM32H7xx/Include
    ${CMSIS_DIR}/Include
)

file(GLOB HAL_SOURCES
    "${HAL_SRC_DIR}/stm32h7xx_hal.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_cortex.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_gpio.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_rcc.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_rcc_ex.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_tim.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_tim_ex.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_uart.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_uart_ex.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_pwr.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_pwr_ex.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_flash.c"
    "${HAL_SRC_DIR}/stm32h7xx_hal_flash_ex.c"
)

set(APP_SOURCES
    Core/Src/main.c
    Modules/capture/sd_capture.c
    Modules/sync/sd_sync.c
    Modules/export/sd_export.c
    Modules/status/sd_status.c
    Modules/validation/sd_validation.c
    Drivers/startup_stm32h723zgtx.s
    Drivers/system_stm32h7xx.c
)

add_executable(sd_measure.elf ${APP_SOURCES} ${HAL_SOURCES})

# Generate .bin and .hex for flashing
add_custom_command(TARGET sd_measure.elf POST_BUILD
    COMMAND arm-none-eabi-objcopy -O ihex   sd_measure.elf sd_measure.hex
    COMMAND arm-none-eabi-objcopy -O binary sd_measure.elf sd_measure.bin
    COMMAND arm-none-eabi-size sd_measure.elf
    COMMENT "Generating sd_measure.hex and sd_measure.bin"
)
