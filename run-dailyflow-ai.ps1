param(
    [string]$PythonPath = '',
    [string]$DataDir = '',
    [string]$CoreDir = '',
    [string]$Binary = '',
    [string]$Bundle = '',
    [switch]$Hidden,
    [int]$TestRemotePort = 0
)
$ErrorActionPreference = 'Stop'
$taskCandidates = @()
if ($PythonPath) {
    $taskCandidates = @($PythonPath)
} else {
    if ($env:DAILYFLOW_PYTHON) { $taskCandidates += $env:DAILYFLOW_PYTHON }
    $taskCandidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
    $taskCandidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe')
    $taskCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($taskCommand) { $taskCandidates += $taskCommand.Source }
}
$taskPython = ''
foreach ($taskCandidate in ($taskCandidates | Select-Object -Unique)) {
    if (!(Test-Path -LiteralPath $taskCandidate -PathType Leaf)) { continue }
    try { & $taskCandidate -c 'import sys; import cryptography; sys.exit(sys.version_info < (3, 10))' 2>$null } catch { continue }
    if ($LASTEXITCODE -eq 0) { $taskPython = $taskCandidate; break }
}
if (!$taskPython) {
    throw '找不到包含 cryptography 的现有 Python 3.10+。请用 -PythonPath 指定已有环境；启动器不会自动安装依赖。'
}
$taskArguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'tools\launch_desktop_flow.py'))
if ($DataDir) { $taskArguments += @('--data-dir', $DataDir) }
if ($CoreDir) { $taskArguments += @('--core-dir', $CoreDir) }
if ($Binary) { $taskArguments += @('--binary', $Binary) }
if ($Bundle) { $taskArguments += @('--bundle', $Bundle) }
if ($Hidden) { $taskArguments += '--hidden' }
if ($TestRemotePort) { $taskArguments += @('--test-remote-port', "$TestRemotePort") }
& $taskPython @taskArguments
if ($LASTEXITCODE -ne 0) { throw "DailyFlow AI 启动失败，退出码 $LASTEXITCODE" }
