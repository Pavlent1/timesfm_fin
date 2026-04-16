from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.contract


REPO_ROOT = Path(__file__).resolve().parents[1]


def find_powershell() -> str:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is not available in this environment.")
    return powershell


def test_run_crypto_prediction_backtest_wrapper_builds_expected_python_command(
    tmp_path: Path,
) -> None:
    powershell = find_powershell()
    python_cmd = tmp_path / "python.cmd"
    python_log = tmp_path / "python.log"
    python_cmd.write_text(
        "@echo off\r\n"
        f">> \"{python_log}\" echo %*\r\n"
        "exit /b 0\r\n",
        encoding="ascii",
    )

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path};{env['PATH']}"

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "run_crypto_prediction_backtest.ps1"),
            "-Symbol",
            "ETHUSDT",
            "-Day",
            "2024-04-01",
            "-Days",
            "3",
            "-HistoryLen",
            "90",
            "-FutureCandles",
            "7",
            "-WindowMinutes",
            "10",
            "-Stride",
            "4",
            "-MaxWindows",
            "5",
            "-UpPrice",
            "0.47",
            "-DownPrice",
            "0.53",
            "-OutputReport",
            "outputs/report.txt",
            "-OutputCsv",
            "outputs/detail.csv",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    logged_command = python_log.read_text(encoding="utf-8").strip()

    assert "Running crypto prediction backtest" in result.stdout
    assert "src\\crypto_prediction_backtest.py" in logged_command
    assert "--symbol ETHUSDT" in logged_command
    assert "--day 2024-04-01" in logged_command
    assert "--days 3" in logged_command
    assert "--history-len 90" in logged_command
    assert "--future-candles 7" in logged_command
    assert "--window-minutes 10" in logged_command
    assert "--stride 4" in logged_command
    assert "--max-windows 5" in logged_command
    assert "--up-price 0.47" in logged_command
    assert "--down-price 0.53" in logged_command
    assert "--output-report outputs/report.txt" in logged_command
    assert "--output-csv outputs/detail.csv" in logged_command
