param(
    [string]$ImageName = "timesfm-fin",
    [string]$Symbol = "BTCUSDT",
    [string]$Day = "",
    [int]$Days = 1,
    [int]$ContextLen = 512,
    [int]$HorizonLen = 16,
    [int]$Stride = 1,
    [int]$BatchSize = 64,
    [string]$Backend = "cpu",
    [string]$OutputCsv = "",
    [int]$Freq = 0,
    [Nullable[int]]$MaxWindows = $null,
    [string]$PostgresHost = "host.docker.internal",
    [int]$PostgresPort = 54329,
    [string]$PostgresDb = "timesfm_fin",
    [string]$PostgresUser = "timesfm",
    [string]$PostgresPassword = "timesfm_dev",
    [string]$HfCacheDir = "",
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
$resolvedHfCacheDir = if ($HfCacheDir -ne "") {
    $HfCacheDir
} elseif ($env:USERPROFILE) {
    Join-Path $env:USERPROFILE ".cache\huggingface"
} else {
    Join-Path $HOME ".cache\huggingface"
}
$null = New-Item -ItemType Directory -Path $resolvedHfCacheDir -Force
$resolvedHfCacheDir = (Resolve-Path $resolvedHfCacheDir).Path
$defaultRepoCachePath = Join-Path $resolvedHfCacheDir "hub\models--pfnet--timesfm-1.0-200m-fin"
$useOfflineWeights = Test-Path $defaultRepoCachePath

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
    "-e", "HF_HOME=/root/.cache/huggingface",
    "-e", "HUGGINGFACE_HUB_CACHE=/root/.cache/huggingface/hub",
    "-v", "${resolvedRepoRoot}:/workspace",
    "-v", "${resolvedHfCacheDir}:/root/.cache/huggingface",
    "--entrypoint", "python"
)

if ($useOfflineWeights) {
    $containerArgs += @("-e", "HF_HUB_OFFLINE=1")
}

$containerArgs += @(
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

if (-not $Live) {
    $containerArgs += @("--days", "$Days")
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

Write-Host "Running crypto minute backtest from '$resolvedRepoRoot' with PostgreSQL at ${PostgresHost}:$PostgresPort and HF cache at '$resolvedHfCacheDir'..."
if ($useOfflineWeights) {
    Write-Host "Using cached Hugging Face weights in offline mode."
}
Invoke-CheckedCommand "docker" @containerArgs
