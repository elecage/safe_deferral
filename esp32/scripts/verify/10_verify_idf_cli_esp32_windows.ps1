# ==============================================================================
# Script: 10_verify_idf_cli_esp32_windows.ps1
# Purpose: Verify ESP-IDF CLI and core build tools on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [10_verify_idf_cli_esp32_windows] Verifying ESP-IDF CLI and core tools...'

$WorkspaceDir = Join-Path $HOME 'esp32_workspace'
$EnvFile = Join-Path $WorkspaceDir '.env.ps1'

if (-not (Test-Path $EnvFile)) {
    throw ".env.ps1 file not found at $EnvFile. Please run configure scripts first."
}
. $EnvFile

if (-not $IDF_PATH -or -not (Test-Path (Join-Path $IDF_PATH 'export.ps1'))) {
    throw 'IDF_PATH is not configured correctly or export.ps1 is missing. Please install ESP-IDF first.'
}

. (Join-Path $IDF_PATH 'export.ps1') | Out-Null

if (-not (Get-Command idf.py -ErrorAction SilentlyContinue)) { throw 'idf.py is not available after sourcing export.ps1.' }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python is not available.' }
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) { throw 'cmake is not available.' }
if (-not (Get-Command ninja -ErrorAction SilentlyContinue)) { throw 'ninja is not available.' }

$esptoolAvailable = $false
if (Get-Command esptool.py -ErrorAction SilentlyContinue) {
    $esptoolAvailable = $true
} else {
    try {
        python -m esptool version | Out-Null
        $esptoolAvailable = $true
    } catch {
        $esptoolAvailable = $false
    }
}
if (-not $esptoolAvailable) { throw 'esptool is not available.' }

Write-Host '  [INFO] Tool versions:'
idf.py --version | ForEach-Object { Write-Host "    - $_" }
python --version 2>&1 | ForEach-Object { Write-Host "    - $_" }
cmake --version | Select-Object -First 1 | ForEach-Object { Write-Host "    - $_" }
ninja --version | ForEach-Object { Write-Host "    - ninja $_" }
if (Get-Command esptool.py -ErrorAction SilentlyContinue) {
    esptool.py version | ForEach-Object { Write-Host "    - $_" }
} else {
    python -m esptool version | ForEach-Object { Write-Host "    - $_" }
}

Write-Host '==> [PASS] ESP-IDF CLI verification completed successfully for Windows.'
