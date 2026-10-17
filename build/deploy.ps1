# QuickFind deploy script: copy the freshly built exe over the installed copy and restart it.
# Usage: powershell -ExecutionPolicy Bypass -File deploy.ps1

$ErrorActionPreference = 'Continue'

$Root = Split-Path -Parent $PSScriptRoot
$Rel  = Join-Path $Root 'release'
$new  = Join-Path $Rel  'QuickFind.exe'
$dst  = Join-Path $env:LOCALAPPDATA 'Programs\QuickFind\QuickFind.exe'

if (-not (Test-Path $new)) { Write-Error "not built yet: $new"; exit 1 }
if (-not (Test-Path (Split-Path $dst))) { Write-Error "not installed: $dst"; exit 1 }

Write-Output '=== 1) kill QuickFind ==='
Get-Process QuickFind -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output ("   kill pid=" + $_.Id)
    try { $_.Kill() } catch {}
}
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 400
    if (-not (Get-Process QuickFind -ErrorAction SilentlyContinue)) { break }
}
if (Get-Process QuickFind -ErrorAction SilentlyContinue) { Write-Error 'still alive'; exit 1 }

Write-Output '=== 2) copy ==='
$ok = $false
for ($i = 0; $i -lt 10; $i++) {
    try { Copy-Item $new $dst -Force -ErrorAction Stop; $ok = $true; break }
    catch { Start-Sleep -Milliseconds 500 }
}
if (-not $ok) { Write-Error 'copy failed (file locked)'; exit 1 }
$fi = Get-Item $dst
Write-Output ("   OK  " + [Math]::Round($fi.Length / 1MB, 2) + " MB  " + $fi.LastWriteTime)

Write-Output '=== 3) start ==='
Start-Process $dst
Start-Sleep -Seconds 8
Get-Process QuickFind -ErrorAction SilentlyContinue | Select-Object Id, StartTime | Format-Table -AutoSize

Write-Output '=== 4) log tail ==='
Get-Content (Join-Path (Split-Path $dst) 'quickfind.log') -Encoding UTF8 -Tail 4
