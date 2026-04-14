param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

Write-Host "Checking Python version from '$PythonExe'..."
$version = & $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to run '$PythonExe'. Install Python 3.10 first, then rerun this script."
}

if (-not $version.StartsWith("3.10.")) {
    throw "This repo currently needs Python 3.10 for TimesFM v1. Found Python $version."
}

$venvPath = Join-Path $PSScriptRoot "..\\.venv"
$venvPython = Join-Path $venvPath "Scripts\\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment at '$venvPath'..."
    Invoke-CheckedCommand $PythonExe -m venv $venvPath
}

Write-Host "Upgrading pip..."
Invoke-CheckedCommand $venvPython -m pip install --upgrade pip

Write-Host "Installing inference dependencies..."
Invoke-CheckedCommand $venvPython -m pip install -r (Join-Path $PSScriptRoot "..\\requirements.inference.txt")

Write-Host ""
Write-Host "Environment ready."
Write-Host "Activate it with:"
Write-Host "  .\\.venv\\Scripts\\Activate.ps1"
