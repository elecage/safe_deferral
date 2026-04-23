# ==============================================================================
# Script: 20_prepare_idf_workspace_esp32_windows.ps1
# Purpose: Prepare common ESP32 workspace directories on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [20_prepare_idf_workspace_esp32_windows] Preparing ESP32 workspace...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'

if (-not (Test-Path $EnvFile)) {
    throw ".env.ps1 file not found at $EnvFile. Please run 10_write_env_files_esp32_windows.ps1 first."
}

. $EnvFile

$TargetWorkspace = if ($ESP32_WORKSPACE_DIR) { $ESP32_WORKSPACE_DIR } else { $WorkspaceDir }
$SampleProjectDir = if ($ESP32_SAMPLE_PROJECT_DIR) { $ESP32_SAMPLE_PROJECT_DIR } else { Join-Path $TargetWorkspace 'samples\hello_idf' }
$BuildLogDir = if ($ESP32_BUILD_LOG_DIR) { $ESP32_BUILD_LOG_DIR } else { Join-Path $TargetWorkspace 'logs' }
$ArtifactDir = Join-Path $TargetWorkspace 'artifacts'
$ManagedComponentsCacheDir = Join-Path $TargetWorkspace 'managed_components_cache'

$dirs = @(
    $TargetWorkspace,
    (Join-Path $TargetWorkspace 'samples'),
    $BuildLogDir,
    $ArtifactDir,
    $ManagedComponentsCacheDir,
    $SampleProjectDir
)
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "  [OK] Workspace prepared at $TargetWorkspace."
Write-Host "  [INFO] Sample project path: $SampleProjectDir"
Write-Host "  [INFO] Build log path: $BuildLogDir"
Write-Host "  [INFO] Artifact path: $ArtifactDir"
Write-Host '==> [PASS] ESP32 workspace preparation completed for Windows.'
