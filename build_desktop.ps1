$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (Test-Path "$PSScriptRoot\AITradingDesktop.exe") {
    $runningDesktop = Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -eq "$PSScriptRoot\AITradingDesktop.exe"
    }
    if ($runningDesktop) {
        throw "Tutup AITradingDesktop dan Stop Bot sebelum build ulang."
    }
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment tidak ditemukan. Jalankan: python -m venv .venv"
}

& ".\.venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v

& ".\.venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "AITradingDesktop" `
    --version-file "version_info.txt" `
    --collect-all sklearn `
    --hidden-import MetaTrader5 `
    --hidden-import pandas `
    --hidden-import joblib `
    desktop_app.py

Copy-Item -LiteralPath "$PSScriptRoot\dist\AITradingDesktop.exe" `
    -Destination "$PSScriptRoot\AITradingDesktop.exe" -Force

Write-Host ""
Write-Host "Build selesai: $PSScriptRoot\AITradingDesktop.exe"

$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
    & $iscc "$PSScriptRoot\installer.iss"
    Write-Host "Installer selesai: $PSScriptRoot\installer_output\AITradingDesktop-Setup-1.2.0.exe"
}
else {
    Write-Warning "Inno Setup belum tersedia; EXE portable selesai tetapi Setup.exe belum dibuat."
}
