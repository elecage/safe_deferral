# ==============================================================================
# Script: 10_write_env_files_esp32_windows.ps1
# Purpose: Generate or append common ESP32 development environment variables on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [10_write_env_files_esp32_windows] Configuring common ESP32 environment variables...'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..\..\..')
$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'
$FirmwareTemplateDir = Join-Path $ProjectRoot 'esp32\firmware\templates\minimal_node'

New-Item -ItemType Directory -Force -Path $WorkspaceDir | Out-Null

if (-not (Test-Path $EnvFile)) {
@"
# ====================================================
# ESP32 Development Environment Variables (Windows)
# ====================================================
"@ | Set-Content -Path $EnvFile -Encoding UTF8
    Write-Host "  [OK] Created $EnvFile."
} else {
    Write-Host "  [INFO] $EnvFile already exists. Appending only missing keys."
}

function Add-EnvVarIfMissing {
    param(
        [string]$Key,
        [string]$Value,
        [string]$Comment = ''
    )

    $existing = Select-String -Path $EnvFile -Pattern "^\`$$Key\s*=|^$Key\s*=" -Quiet -ErrorAction SilentlyContinue
    if (-not $existing) {
        if ($Comment) {
            Add-Content -Path $EnvFile -Value ""
            Add-Content -Path $EnvFile -Value "# $Comment"
        }
        Add-Content -Path $EnvFile -Value "`$$Key = '$Value'"
        Write-Host "  [OK] Appended missing key: $Key"
    }
}

Add-EnvVarIfMissing -Key 'ESP32_WORKSPACE_DIR' -Value $WorkspaceDir -Comment 'Common ESP32 Workspace Settings'
Add-EnvVarIfMissing -Key 'ESP_ROOT' -Value (Join-Path $HOME 'esp')
Add-EnvVarIfMissing -Key 'IDF_PATH' -Value (Join-Path (Join-Path $HOME 'esp') 'esp-idf')
Add-EnvVarIfMissing -Key 'IDF_TOOLS_PATH' -Value (Join-Path $HOME '.espressif')
Add-EnvVarIfMissing -Key 'ESP_IDF_GIT_REF' -Value '' -Comment 'Optional ESP-IDF Git Ref (leave empty to use current checked-out ref)'
Add-EnvVarIfMissing -Key 'IDF_TARGET' -Value 'esp32' -Comment 'Default ESP-IDF Build Target'
Add-EnvVarIfMissing -Key 'ESP32_FIRMWARE_TEMPLATE_DIR' -Value $FirmwareTemplateDir
Add-EnvVarIfMissing -Key 'ESP32_SAMPLE_PROJECT_DIR' -Value (Join-Path $WorkspaceDir 'samples\hello_idf')
Add-EnvVarIfMissing -Key 'ESP32_BUILD_LOG_DIR' -Value (Join-Path $WorkspaceDir 'logs')
Add-EnvVarIfMissing -Key 'ESPPORT' -Value '' -Comment 'Optional serial port override (for example: COM3)'
Add-EnvVarIfMissing -Key 'ESPBAUD' -Value '460800'

Write-Warning "Review IDF_PATH, ESP_IDF_GIT_REF, and ESPPORT in $EnvFile."
Write-Host '==> [PASS] ESP32 common environment variables configured for Windows.'
