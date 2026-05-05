$ErrorActionPreference = "Stop"

$projectDir = "E:\smartpet_ascii"
$venvPython = Join-Path $projectDir ".venv\Scripts\python.exe"
$appName = "AnyaPet"
$iconPath = Join-Path $projectDir "assets\app_icon.ico"

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python not found: $venvPython"
}

if (-not (Test-Path $iconPath)) {
    throw "App icon not found: $iconPath"
}

Push-Location $projectDir
try {
    & $venvPython -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name $appName `
        --icon $iconPath `
        --add-data "assets;assets" `
        --add-data ".env;." `
        gui_app.py
}
finally {
    Pop-Location
}

Write-Host "Build complete: $projectDir\dist\$appName"
