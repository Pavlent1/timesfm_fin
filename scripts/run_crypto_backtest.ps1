param(
    [string]$ImageName = "timesfm-fin",
    [string]$Symbol = "BTCUSDT",
    [string]$Day = "",
    [int]$ContextLen = 512,
    [int]$HorizonLen = 16,
    [int]$Stride = 1,
    [int]$BatchSize = 64,
    [string]$Backend = "gpu",
    [string]$OutputCsv = "",
    [int]$Freq = 0,
    [Nullable[int]]$MaxWindows = $null,
    [string]$PostgresHost = "host.docker.internal",
    [int]$PostgresPort = 54329,
    [string]$PostgresDb = "timesfm_fin",
    [string]$PostgresUser = "timesfm",
    [string]$PostgresPassword = "timesfm_dev",
    [switch]$Live,
    [switch]$SkipBuild
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

$repoRoot = Split-Path -Parent $PSScriptRoot
$resolvedRepoRoot = (Resolve-Path $repoRoot).Path

if (-not $SkipBuild) {
    Write-Host "Building Docker image '$ImageName'..."
    Invoke-CheckedCommand "docker" "build" "-t" $ImageName $resolvedRepoRoot
}

$containerArgs = @(
    "run",
    "--rm"
)

if ($Backend -eq "gpu") {
    $containerArgs += @("--gpus", "all")
}

$containerArgs += @(
    "--add-host", "host.docker.internal:host-gateway",
    "-e", "POSTGRES_HOST=$PostgresHost",
    "-e", "POSTGRES_PORT=$PostgresPort",
    "-e", "POSTGRES_DB=$PostgresDb",
    "-e", "POSTGRES_USER=$PostgresUser",
    "-e", "POSTGRES_PASSWORD=$PostgresPassword",
    "-v", "${resolvedRepoRoot}:/workspace",
    "--entrypoint", "python",
    $ImageName,
    "src/crypto_minute_backtest.py",
    "--symbol", $Symbol,
    "--context-len", "$ContextLen",
    "--horizon-len", "$HorizonLen",
    "--stride", "$Stride",
    "--batch-size", "$BatchSize",
    "--backend", $Backend,
    "--freq", "$Freq"
)

if ($Day -ne "") {
    $containerArgs += @("--day", $Day)
}

if ($null -ne $MaxWindows) {
    $containerArgs += @("--max-windows", "$MaxWindows")
}

if ($Live) {
    $containerArgs += @("--mode", "live")
}

if ($OutputCsv -ne "") {
    $containerArgs += @("--output-csv", $OutputCsv)
}

Write-Host "Running crypto minute backtest from '$resolvedRepoRoot' with PostgreSQL at ${PostgresHost}:$PostgresPort..."
Invoke-CheckedCommand "docker" @containerArgs
