# Compila RevienDocker a un único .exe (dist\RevienDocker.exe).
# Requisitos: pip install -r requirements.txt -r requirements-dev.txt
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python src\studio_icon.py
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name RevienDocker --icon web\assets\icon.ico `
    --paths src --manifest tools\app.manifest `
    --add-data "web\index.html;web" --add-data "web\studio.css;web" --add-data "web\studio.js;web" --add-data "web\studio_icons.js;web" `
    --add-data "web\assets\icon.png;web\assets" --add-data "web\assets\brand-icon.png;web\assets" --add-data "web\assets\wordmark.svg;web\assets" --add-data "web\assets\logo-switch.jpg;web\assets" `
    --collect-submodules webview --collect-submodules pycaw --hidden-import pystray._win32 src\studio_app.py
Remove-Item -Recurse -Force build, RevienDocker.spec -ErrorAction SilentlyContinue
Write-Host "Listo: $(Get-Location)\dist\RevienDocker.exe"
