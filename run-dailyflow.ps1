param([switch]$Hidden, [switch]$Detach, [int]$Port = 8171, [string]$AppData = '')
$ErrorActionPreference = 'Stop'
$taskWorkspace = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
$env:PYTHONUTF8 = '1'
$env:OCTO_HUB = Join-Path $taskWorkspace 'OctoSense-App-Hub\target\release\hub.exe'
$env:OCTO_CARD_HOST = Join-Path $taskWorkspace 'OctoSense-App-Hub\target\release\card-host.exe'
foreach ($taskExecutable in @($taskPython, $env:OCTO_HUB, $env:OCTO_CARD_HOST)) {
    if (!(Test-Path -LiteralPath $taskExecutable -PathType Leaf)) { throw "Missing executable: $taskExecutable" }
}
if (!$Hidden) { Remove-Item Env:MAKEPAD_HIDE_WINDOWS -ErrorAction SilentlyContinue }
$taskArguments = @('-X','utf8',(Join-Path $taskWorkspace 'OctoScript-App-Design-Flow\tools\octo'),'run',(Join-Path $PSScriptRoot 'bundle'),'--port',"$Port")
if ($Hidden) { $taskArguments += '--hidden' }
if ($Detach) { $taskArguments += '--detach' }
if ($AppData) { $taskArguments += @('--app-data', $AppData) }
& $taskPython @taskArguments
if ($LASTEXITCODE -ne 0) { throw "DailyFlow exited with code $LASTEXITCODE" }
