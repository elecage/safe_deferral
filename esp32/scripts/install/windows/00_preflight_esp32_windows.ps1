# ==============================================================================
# Script: 00_preflight_esp32_windows.ps1
# Purpose: Preflight checks for ESP32 development on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [00_preflight_esp32_windows] Checking Windows ESP32 development prerequisites...'

if ($PSVersionTable.PSVersion.Major -lt 5) {
    throw 'PowerShell 5 or newer is required.'
}
Write-Host '  [OK] PowerShell version is sufficient.'

if (-not $IsWindows) {
    throw 'This script must be run on Windows PowerShell or PowerShell on Windows.'
}
Write-Host '  [OK] Operating system is Windows.'

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host '  [OK] winget is available.'
} else {
    Write-Warning 'winget is not available. Automatic prerequisite installation may be limited.'
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host '  [OK] git is available.'
} else {
    Write-Warning 'git is not installed yet. It will be installed in the next step.'
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "  [OK] Python is available ($pyver)."
} else {
    Write-Warning 'python is not installed yet. It will be installed in the next step.'
}

$drive = Get-PSDrive -Name $HOME.Substring(0,1)
$freeGB = [math]::Round($drive.Free / 1GB, 0)
if ($freeGB -lt 10) {
    Write-Warning "Less than 10GB of free space is available (${freeGB}GB)."
} else {
    Write-Host "  [OK] Disk space looks sufficient (${freeGB}GB available)."
}

try {
    Test-Connection github.com -Count 1 -Quiet | Out-Null
    Write-Host '  [OK] Network access appears available.'
} catch {
    Write-Warning 'Network access check failed. Online installation may fail.'
}

Write-Host '==> [PASS] Windows preflight completed.'
