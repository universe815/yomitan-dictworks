[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OaldDirectory,

    [int]$Port = 5051,

    [switch]$RebuildIndex
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$sourceRoot = (Resolve-Path -LiteralPath $OaldDirectory).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$mdx = Join-Path $sourceRoot 'oaldpe.mdx'
$index = Join-Path $projectRoot 'generated\oald-audio-index.json'
$report = Join-Path $projectRoot 'generated\oald-audio-report.json'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Missing .venv. Run: py -3 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
}
if (-not (Test-Path -LiteralPath $mdx -PathType Leaf)) {
    throw "Missing source dictionary: $mdx"
}

$mdds = @(
    Get-ChildItem -LiteralPath $sourceRoot -Filter 'oaldpe*.mdd' -File |
        Sort-Object -Property Name
)
if ($mdds.Count -eq 0) {
    throw "No OALD companion MDD files found under: $sourceRoot"
}

$indexNeedsBuild = $RebuildIndex -or -not (Test-Path -LiteralPath $index -PathType Leaf)
if (-not $indexNeedsBuild) {
    $indexNeedsBuild = (Get-Item -LiteralPath $index).LastWriteTimeUtc -lt (
        Get-Item -LiteralPath $mdx
    ).LastWriteTimeUtc
}

if ($indexNeedsBuild) {
    & $python (Join-Path $projectRoot 'scripts\build_oald_audio_index.py') `
        --mdx $mdx `
        --output $index `
        --report $report
    if ($LASTEXITCODE -ne 0) {
        throw "OALD audio index build failed with exit code $LASTEXITCODE"
    }
}

$serverArguments = @(
    (Join-Path $projectRoot 'scripts\oald_audio_server.py'),
    '--index',
    $index,
    '--port',
    $Port
)
foreach ($mdd in $mdds) {
    $serverArguments += @('--mdd', $mdd.FullName)
}

Write-Host "Starting OALD UK/US audio on http://127.0.0.1:$Port/"
Write-Host 'Keep this PowerShell window open while using Yomitan.'
& $python @serverArguments
