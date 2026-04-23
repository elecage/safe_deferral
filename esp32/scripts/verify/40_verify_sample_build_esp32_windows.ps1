# ==============================================================================
# Script: 40_verify_sample_build_esp32_windows.ps1
# Purpose: Verify that a sample ESP-IDF project can be built successfully on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [40_verify_sample_build_esp32_windows] Verifying sample ESP-IDF build...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'
if (-not (Test-Path $EnvFile)) { throw ".env.ps1 file not found at $EnvFile." }
. $EnvFile

if (-not $IDF_PATH -or -not (Test-Path (Join-Path $IDF_PATH 'export.ps1'))) {
    throw 'IDF_PATH is not configured correctly or export.ps1 is missing.'
}
$SampleProjectDir = if ($ESP32_SAMPLE_PROJECT_DIR) { $ESP32_SAMPLE_PROJECT_DIR } else { Join-Path $WorkspaceDir 'samples\hello_idf' }
$Target = if ($IDF_TARGET) { $IDF_TARGET } else { 'esp32' }
$LogDir = if ($ESP32_BUILD_LOG_DIR) { $ESP32_BUILD_LOG_DIR } else { Join-Path $WorkspaceDir 'logs' }
$BuildLogFile = Join-Path $LogDir 'sample_build.log'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $SampleProjectDir)) {
    throw "Sample project not found at $SampleProjectDir. Please run 40_prepare_sample_project_esp32_windows.ps1 first."
}

. (Join-Path $IDF_PATH 'export.ps1') | Out-Null
Set-Location $SampleProjectDir
Write-Host "  [INFO] Running clean build for target $Target ..."
idf.py set-target $Target | Out-Null
try { idf.py fullclean | Out-Null } catch { }
idf.py build 2>&1 | Tee-Object -FilePath $BuildLogFile

if (-not (Test-Path (Join-Path $SampleProjectDir 'build\hello_world.bin'))) {
    throw "Sample binary hello_world.bin was not generated. Check $BuildLogFile for build errors."
}
if (-not (Test-Path (Join-Path $SampleProjectDir 'build\hello_world.elf'))) {
    throw "Sample ELF hello_world.elf was not generated. Check $BuildLogFile for build errors."
}

Write-Host '  [OK] Sample build artifacts were generated successfully.'
Write-Host "  [INFO] Build log written to $BuildLogFile."
Write-Host '==> [PASS] Sample ESP-IDF build verification completed for Windows.'
