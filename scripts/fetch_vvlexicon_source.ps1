param(
  [string]$Output = "data/vvlexicon/headwords.js"
)

$ErrorActionPreference = 'Stop'
$uri = 'https://www2.ninjal.ac.jp/vvlexicon/js/headwords.js'
$destination = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Output))
$parent = Split-Path -Parent $destination
New-Item -ItemType Directory -Force -Path $parent | Out-Null

Invoke-WebRequest -Uri $uri -OutFile $destination
$prefix = [System.IO.File]::ReadAllText($destination, [System.Text.Encoding]::UTF8).TrimStart([char]0xFEFF)
if (-not $prefix.StartsWith('var headwords = [')) {
  Remove-Item -LiteralPath $destination -Force
  throw "下载内容不是预期的 NINJAL headwords.js：$uri"
}

Write-Output "已保存 NINJAL 词条源文件：$destination"
Write-Output '该文件用于本地转换；请先确认 NINJAL 的数据使用条件，再决定是否分享生成的词典。'
