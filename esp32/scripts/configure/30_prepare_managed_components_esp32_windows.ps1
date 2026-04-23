# ==============================================================================
# Script: 30_prepare_managed_components_esp32_windows.ps1
# Purpose: Prepare managed component cache and optional project-level placeholder on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [30_prepare_managed_components_esp32_windows] Preparing managed component workspace...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'

if (-not (Test-Path $EnvFile)) {
    throw ".env.ps1 file not found at $EnvFile. Please run 10_write_env_files_esp32_windows.ps1 first."
}

. $EnvFile

$TargetWorkspace = if ($ESP32_WORKSPACE_DIR) { $ESP32_WORKSPACE_DIR } else { $WorkspaceDir }
$SampleProjectDir = if ($ESP32_SAMPLE_PROJECT_DIR) { $ESP32_SAMPLE_PROJECT_DIR } else { Join-Path $TargetWorkspace 'samples\hello_idf' }
$ManagedComponentsCacheDir = Join-Path $TargetWorkspace 'managed_components_cache'
$ComponentPlaceholderFile = Join-Path $SampleProjectDir 'idf_component.yml'

New-Item -ItemType Directory -Force -Path $ManagedComponentsCacheDir | Out-Null
New-Item -ItemType Directory -Force -Path $SampleProjectDir | Out-Null

if (-not (Test-Path $ComponentPlaceholderFile)) {
@"
# Placeholder managed component manifest for future bounded node firmware.
dependencies:
"@ | Set-Content -Path $ComponentPlaceholderFile -Encoding UTF8
    Write-Host "  [OK] Created placeholder $ComponentPlaceholderFile."
} else {
    Write-Host "  [INFO] $ComponentPlaceholderFile already exists. Leaving it unchanged."
}

Write-Host "  [OK] Managed component cache directory prepared at $ManagedComponentsCacheDir."
Write-Host '==> [PASS] Managed component workspace preparation completed for Windows.'
