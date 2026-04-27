# ==============================================================================
# Script: 10_install_prereqs_esp32_windows.ps1
# Purpose: Install prerequisite packages for ESP32 development on Windows
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [10_install_prereqs_esp32_windows] Installing Windows prerequisites for ESP32 development...'

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'winget is required for this installer. Please install winget or install the prerequisites manually.'
}

$packages = @(
    @{ Id = 'Git.Git'; Name = 'Git' },
    @{ Id = 'Python.Python.3.11'; Name = 'Python 3.11' },
    @{ Id = 'Kitware.CMake'; Name = 'CMake' },
    @{ Id = 'Ninja-build.Ninja'; Name = 'Ninja' }
)

foreach ($pkg in $packages) {
    Write-Host "  [INFO] Installing $($pkg.Name) via winget..."
    winget install --id $($pkg.Id) --exact --silent --accept-source-agreements --accept-package-agreements
}

Write-Warning 'dfu-util and USB serial drivers are not installed automatically by this script.'
Write-Warning 'If your ESP32 board requires CP210x/CH340 drivers, install them separately.'

Write-Host '==> [PASS] Windows prerequisites installation completed.'
