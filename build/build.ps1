# QuickFind build script
# Usage: right-click -> Run with PowerShell, or:  powershell -File build.ps1
# Paths are derived from the script location, so this file stays pure ASCII.

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot          # ...\QuickFind
$Src  = Join-Path $Root 'src'
$Rel  = Join-Path $Root 'release'
$Wk   = Join-Path $Root 'build\work'
$Wk2  = Join-Path $Root 'build\work2'
$Spc  = Join-Path $Root 'build'
$Py   = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Py) { $Py = (Get-Command py -ErrorAction SilentlyContinue).Source }

if (-not $Py) {
    Write-Error 'Python 3.10+ not found. Install it or add it to PATH.'
    exit 1
}
if (-not (Test-Path $Rel)) { New-Item -ItemType Directory -Path $Rel -Force | Out-Null }

$env:PYTHONUTF8 = '1'
Set-Location $Src

Write-Output '=== 1/2 build QuickFind.exe ==='
& $Py -m PyInstaller --noconfirm --onefile --windowed --name QuickFind `
    --icon (Join-Path $Root 'assets\quickfind.ico') `
    --add-data "$(Join-Path $Root 'assets\quickfind.ico');assets" `
    --distpath $Rel --workpath $Wk --specpath $Spc (Join-Path $Src 'quickfind.py')
if ($LASTEXITCODE -ne 0) { Write-Error 'build QuickFind.exe FAILED'; exit 1 }

Write-Output '=== 2/2 build QuickFind-Setup.exe ==='
& $Py -m PyInstaller --noconfirm --onefile --console --name QuickFind-Setup `
    --add-binary "$(Join-Path $Rel 'QuickFind.exe');." `
    --distpath $Rel --workpath $Wk2 --specpath $Spc (Join-Path $Src 'installer.py')
if ($LASTEXITCODE -ne 0) { Write-Error 'build QuickFind-Setup.exe FAILED'; exit 1 }

Write-Output ''
Write-Output '=== done ==='
Get-ChildItem $Rel -Filter *.exe |
    Select-Object Name, @{n = 'MB'; e = { [Math]::Round($_.Length / 1MB, 2) } }, LastWriteTime |
    Format-Table -AutoSize
