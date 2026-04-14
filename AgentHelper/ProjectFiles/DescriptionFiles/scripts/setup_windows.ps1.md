# `scripts/setup_windows.ps1`

This PowerShell helper bootstraps a Windows virtual environment for the repo's inference path. It verifies that the selected Python executable is Python 3.10, creates `.venv` when missing, upgrades `pip`, and installs the packages from `requirements.inference.txt`.

The script uses a small `Invoke-CheckedCommand` wrapper so failed subprocesses stop the setup immediately, including a failure message that safely interpolates the subprocess exit code in PowerShell. It does not run model code itself; its side effects are environment creation and package installation under the repo root.

Category: developer setup script.
