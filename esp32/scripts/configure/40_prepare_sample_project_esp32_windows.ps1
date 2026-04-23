# ==============================================================================
# Script: 40_prepare_sample_project_esp32_windows.ps1
# Purpose: Prepare a sample ESP-IDF project for environment verification on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [40_prepare_sample_project_esp32_windows] Preparing sample ESP-IDF project...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'

if (-not (Test-Path $EnvFile)) {
    throw ".env.ps1 file not found at $EnvFile. Please run 10_write_env_files_esp32_windows.ps1 first."
}

. $EnvFile

if (-not $IDF_PATH -or -not (Test-Path $IDF_PATH)) {
    throw 'IDF_PATH is not set correctly in .env.ps1. Please install ESP-IDF first.'
}

$SampleProjectDir = if ($ESP32_SAMPLE_PROJECT_DIR) { $ESP32_SAMPLE_PROJECT_DIR } else { Join-Path $WorkspaceDir 'samples\hello_idf' }
$HelloWorldTemplate = Join-Path $IDF_PATH 'examples\get-started\hello_world'

if (-not (Test-Path $HelloWorldTemplate)) {
    throw "Could not find hello_world example in $HelloWorldTemplate"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SampleProjectDir) | Out-Null
if (Test-Path $SampleProjectDir) {
    Remove-Item -Recurse -Force $SampleProjectDir
}
Copy-Item -Recurse -Force $HelloWorldTemplate $SampleProjectDir

Write-Host "  [OK] Sample project copied to $SampleProjectDir."
Write-Host '==> [PASS] Sample ESP-IDF project preparation completed for Windows.'
