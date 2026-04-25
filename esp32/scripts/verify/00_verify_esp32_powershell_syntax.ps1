# ==============================================================================
# Script: 00_verify_esp32_powershell_syntax.ps1
# Purpose: Verify PowerShell syntax for ESP32 scripts
# ==============================================================================
$ErrorActionPreference = 'Stop'

Write-Host '==> [00_verify_esp32_powershell_syntax] Verifying ESP32 PowerShell script syntax...'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Esp32Root = Resolve-Path (Join-Path $ScriptDir '..\..')
$ScriptsRoot = Join-Path $Esp32Root 'scripts'

if (-not (Test-Path $ScriptsRoot)) {
    throw "ESP32 scripts directory not found: $ScriptsRoot"
}

$ScriptFiles = Get-ChildItem -Path $ScriptsRoot -Recurse -Filter '*.ps1' | Sort-Object FullName

if (-not $ScriptFiles -or $ScriptFiles.Count -eq 0) {
    throw "No ESP32 PowerShell scripts found under $ScriptsRoot"
}

$Failures = 0

foreach ($ScriptFile in $ScriptFiles) {
    $RelativePath = Resolve-Path -Relative $ScriptFile.FullName
    Write-Host "  [INFO] Checking $RelativePath..."

    $Tokens = $null
    $ParseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $ScriptFile.FullName,
        [ref]$Tokens,
        [ref]$ParseErrors
    ) | Out-Null

    if ($ParseErrors -and $ParseErrors.Count -gt 0) {
        Write-Host "    [FATAL] PowerShell syntax errors detected: $RelativePath"
        foreach ($ParseError in $ParseErrors) {
            Write-Host "      Line $($ParseError.Extent.StartLineNumber), Column $($ParseError.Extent.StartColumnNumber): $($ParseError.Message)"
        }
        $Failures = 1
    } else {
        Write-Host '    [OK] Syntax valid.'
    }
}

if ($Failures -ne 0) {
    throw 'One or more ESP32 PowerShell scripts failed syntax checks.'
}

Write-Host '==> [PASS] All ESP32 PowerShell scripts passed syntax checks.'
