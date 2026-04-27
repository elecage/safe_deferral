# ==============================================================================
# Script: 20_verify_toolchain_target_esp32_windows.ps1
# Purpose: Verify target selection for the sample ESP-IDF project on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [20_verify_toolchain_target_esp32_windows] Verifying ESP-IDF target selection...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'
if (-not (Test-Path $EnvFile)) { throw ".env.ps1 file not found at $EnvFile." }
. $EnvFile

if (-not $IDF_PATH -or -not (Test-Path (Join-Path $IDF_PATH 'export.ps1'))) {
    throw 'IDF_PATH is not configured correctly or export.ps1 is missing.'
}
$SampleProjectDir = if ($ESP32_SAMPLE_PROJECT_DIR) { $ESP32_SAMPLE_PROJECT_DIR } else { Join-Path $WorkspaceDir 'samples\hello_idf' }
$Target = if ($IDF_TARGET) { $IDF_TARGET } else { 'esp32' }
if (-not (Test-Path $SampleProjectDir)) {
    throw "Sample project not found at $SampleProjectDir. Please run 30_prepare_sample_project_esp32_windows.ps1 first."
}

. (Join-Path $IDF_PATH 'export.ps1') | Out-Null
Set-Location $SampleProjectDir
Write-Host "  [INFO] Running idf.py set-target $Target ..."
idf.py set-target $Target | Out-Null
Write-Host "  [OK] Target '$Target' was applied successfully."
Write-Host '==> [PASS] ESP-IDF target toolchain verification completed for Windows.'
