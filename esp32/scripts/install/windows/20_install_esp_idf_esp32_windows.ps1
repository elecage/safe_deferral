# ==============================================================================
# Script: 20_install_esp_idf_esp32_windows.ps1
# Purpose: Install ESP-IDF on Windows using the standard PowerShell setup path
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [20_install_esp_idf_esp32_windows] Installing ESP-IDF on Windows...'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git is required. Please run 10_install_prereqs_esp32_windows.ps1 first.'
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'python is required. Please run 10_install_prereqs_esp32_windows.ps1 first.'
}

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'

if (Test-Path $EnvFile) {
    Write-Host "  [INFO] Loading ESP32 environment variables from $EnvFile..."
    . $EnvFile
} else {
    Write-Host "  [INFO] $EnvFile not found. Using built-in ESP-IDF install defaults."
}

$EspRoot = if ($ESP_ROOT) { $ESP_ROOT } elseif ($env:ESP_ROOT) { $env:ESP_ROOT } else { Join-Path $HOME 'esp' }
$IdfPath = if ($IDF_PATH) { $IDF_PATH } elseif ($env:IDF_PATH) { $env:IDF_PATH } else { Join-Path $EspRoot 'esp-idf' }
$IdfGitRef = if ($ESP_IDF_GIT_REF) { $ESP_IDF_GIT_REF } else { $env:ESP_IDF_GIT_REF }
$IdfToolsPath = if ($IDF_TOOLS_PATH) { $IDF_TOOLS_PATH } elseif ($env:IDF_TOOLS_PATH) { $env:IDF_TOOLS_PATH } else { Join-Path $HOME '.espressif' }

New-Item -ItemType Directory -Force -Path $EspRoot | Out-Null
$env:IDF_TOOLS_PATH = $IdfToolsPath

Write-Host '  [INFO] Effective ESP-IDF install settings:'
Write-Host "         - ESP_ROOT=$EspRoot"
Write-Host "         - IDF_PATH=$IdfPath"
Write-Host "         - IDF_TOOLS_PATH=$IdfToolsPath"
if ($IdfGitRef) {
    Write-Host "         - ESP_IDF_GIT_REF=$IdfGitRef"
} else {
    Write-Host '         - ESP_IDF_GIT_REF=<current checkout>'
}

if (-not (Test-Path (Join-Path $IdfPath '.git'))) {
    Write-Host "  [INFO] Cloning ESP-IDF into $IdfPath ..."
    git clone --recursive https://github.com/espressif/esp-idf.git $IdfPath
} else {
    Write-Host "  [INFO] ESP-IDF repository already exists at $IdfPath."
}

Set-Location $IdfPath

if ($IdfGitRef) {
    Write-Host "  [INFO] Checking out requested ESP-IDF ref: $IdfGitRef"
    git fetch --all --tags
    git checkout $IdfGitRef
    git submodule update --init --recursive
} else {
    Write-Warning 'ESP_IDF_GIT_REF is not set. Using the repository''s current checked-out ref.'
}

if (-not (Test-Path (Join-Path $IdfPath 'install.ps1'))) {
    throw "install.ps1 not found in $IdfPath"
}

Write-Host '  [INFO] Running ESP-IDF install.ps1 ...'
& powershell -ExecutionPolicy Bypass -File (Join-Path $IdfPath 'install.ps1')

if (-not (Test-Path (Join-Path $IdfPath 'export.ps1'))) {
    throw 'export.ps1 was not found after installation.'
}

Write-Host '  [OK] ESP-IDF installed.'
Write-Host '  [INFO] To activate the environment in the current shell, run:'
Write-Host "         . $IdfPath\export.ps1"

Write-Host '==> [PASS] ESP-IDF installation completed for Windows.'
