# Compila RevienDocker a un único .exe (dist\RevienDocker.exe).
# Requisitos: pip install -r requirements.txt -r requirements-dev.txt
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python studio_icon.py
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name RevienDocker --icon assets\icon.ico `
    --add-data "index.html;." --add-data "studio.css;." --add-data "studio.js;." --add-data "studio_icons.js;." `
    --add-data "assets\icon.png;assets" --add-data "assets\wordmark.svg;assets" `
    --collect-submodules webview --hidden-import pystray._win32 studio_app.py
Remove-Item -Recurse -Force build, RevienDocker.spec -ErrorAction SilentlyContinue
Write-Host "Listo: $PSScriptRoot\dist\RevienDocker.exe"
