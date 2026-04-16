param(
    [string]$PythonExe = "python",
    [string]$Symbol = "BTCUSDT",
    [string]$Day = "",
    [int]$Days = 1,
    [int]$HistoryLen = 60,
    [int]$FutureCandles = 5,
    [Nullable[int]]$WindowMinutes = $null,
    [int]$Stride = 1,
    [Nullable[int]]$MaxWindows = $null,
    [double]$UpPrice = 0.5,
    [double]$DownPrice = 0.5,
    [string]$OutputReport = "",
    [string]$OutputCsv = ""
)

$ErrorActionPreference = "Stop"

$resolvedDay = $Day
if ($resolvedDay -eq "") {
    $resolvedDay = [DateTime]::UtcNow.AddDays(-1).ToString("yyyy-MM-dd")
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $repoRoot "src\crypto_prediction_backtest.py"

$commandArgs = @(
    $scriptPath,
    "--symbol", $Symbol,
    "--day", $resolvedDay,
    "--days", "$Days",
    "--history-len", "$HistoryLen",
    "--future-candles", "$FutureCandles",
    "--stride", "$Stride",
    "--up-price", "$UpPrice",
    "--down-price", "$DownPrice"
)

if ($null -ne $WindowMinutes) {
    $commandArgs += @("--window-minutes", "$WindowMinutes")
}

if ($null -ne $MaxWindows) {
    $commandArgs += @("--max-windows", "$MaxWindows")
}

if ($OutputReport -ne "") {
    $commandArgs += @("--output-report", $OutputReport)
}

if ($OutputCsv -ne "") {
    $commandArgs += @("--output-csv", $OutputCsv)
}

Write-Host "Running crypto prediction backtest"
& $PythonExe @commandArgs
if ($LASTEXITCODE -ne 0) {
    throw "Crypto prediction backtest failed with exit code ${LASTEXITCODE}."
}
