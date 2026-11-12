# Сборка dist\Eirin.exe через PyInstaller.
# Запуск: powershell -ExecutionPolicy Bypass -File scripts\build.ps1

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Не найдено .venv. Создайте окружение: python -m venv .venv"
}

& $python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller не установлен. Выполните: .venv\Scripts\python.exe -m pip install pyinstaller"
}

if (-not (Test-Path "assets\icon.ico")) {
    & $python scripts\make_icon.py
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name Eirin `
    --icon "assets\icon.ico" `
    --collect-submodules yt_dlp `
    --collect-data yt_dlp `
    "run.py"

if ($LASTEXITCODE -ne 0) {
    throw "Сборка завершилась с ошибкой."
}

Write-Host ""
Write-Host "Готово: $root\dist\Eirin.exe"
Write-Host "Не забудьте про ffmpeg в PATH (и Node.js/Deno для YouTube)."
