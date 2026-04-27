# ==============================================================================
# Script: 30_verify_component_resolution_esp32_windows.ps1
# Purpose: Verify CMake reconfigure and managed component resolution on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [30_verify_component_resolution_esp32_windows] Verifying component resolution...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'
if (-not (Test-Path $EnvFile)) { throw ".env.ps1 file not found at $EnvFile." }
. $EnvFile

if (-not $IDF_PATH -or -not (Test-Path (Join-Path $IDF_PATH 'export.ps1'))) {
    throw 'IDF_PATH is not configured correctly or export.ps1 is missing.'
}
$SampleProjectDir = if ($ESP32_SAMPLE_PROJECT_DIR) { $ESP32_SAMPLE_PROJECT_DIR } else { Join-Path $WorkspaceDir 'samples\hello_idf' }
if (-not (Test-Path $SampleProjectDir)) {
    throw "Sample project not found at $SampleProjectDir. Please run 30_prepare_sample_project_esp32_windows.ps1 first."
}

. (Join-Path $IDF_PATH 'export.ps1') | Out-Null
Set-Location $SampleProjectDir
Write-Host '  [INFO] Running idf.py reconfigure ...'
idf.py reconfigure | Out-Null

if (-not (Test-Path (Join-Path $SampleProjectDir 'build\CMakeCache.txt'))) {
    throw 'CMakeCache.txt was not generated during reconfigure.'
}

Write-Host '  [OK] CMake reconfigure completed successfully.'
if (Test-Path (Join-Path $SampleProjectDir 'managed_components')) {
    Write-Host '  [INFO] managed_components directory is present.'
} else {
    Write-Host '  [INFO] managed_components directory is not present; no managed dependencies may be required yet.'
}

Write-Host '==> [PASS] Component resolution verification completed for Windows.'
