$ErrorActionPreference = "Stop"

# Edit these values before running.
$ImageName = "timesfm-fin"
$Symbol = "BTCUSDT"
$StartDay = "2026-04-13"
$Days = 1
$ContextLen = 512
$HorizonLen = 5
$Stride = 5
$BatchSize = 64
$Backend = "gpu"
$Freq = 0
$MaxWindows = $null
$OutputCsv = ""
$PostgresHost = "host.docker.internal"
$PostgresPort = 54329
$PostgresDb = "timesfm_fin"
$PostgresUser = "timesfm"
$PostgresPassword = "timesfm_dev"
$SkipBuild = $true
$HfCacheDir = Join-Path $env:USERPROFILE ".cache\huggingface"

$wrapperPath = Join-Path $PSScriptRoot "run_crypto_backtest.ps1"
$wrapperArgs = @{
    ImageName = $ImageName
    Symbol = $Symbol
    Day = $StartDay
    Days = $Days
    ContextLen = $ContextLen
    HorizonLen = $HorizonLen
    Stride = $Stride
    BatchSize = $BatchSize
    Backend = $Backend
    Freq = $Freq
    PostgresHost = $PostgresHost
    PostgresPort = $PostgresPort
    PostgresDb = $PostgresDb
    PostgresUser = $PostgresUser
    PostgresPassword = $PostgresPassword
    HfCacheDir = $HfCacheDir
}

if ($SkipBuild) {
    $wrapperArgs.SkipBuild = $true
}

if ($null -ne $MaxWindows) {
    $wrapperArgs.MaxWindows = $MaxWindows
}

if ($OutputCsv -ne "") {
    $wrapperArgs.OutputCsv = $OutputCsv
}

& $wrapperPath @wrapperArgs
if ($LASTEXITCODE -ne 0) {
    throw "Preset crypto backtest run failed with exit code ${LASTEXITCODE}."
}
