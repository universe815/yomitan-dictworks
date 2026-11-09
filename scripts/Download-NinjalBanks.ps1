param([ValidateSet('all','verbs','cases')][string]$Bank='all')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
function Get-CachedFile([string]$Url,[string]$RelativePath) {
    $target=Join-Path $projectRoot $RelativePath
    if(Test-Path -LiteralPath $target){return}
    New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
    for($attempt=1;$attempt -le 3;$attempt++) {
        try {
            Invoke-WebRequest -Uri $Url -OutFile ($target+'.part') -TimeoutSec 30
            Move-Item -LiteralPath ($target+'.part') -Destination $target
            Start-Sleep -Milliseconds 120
            return
        } catch { if($attempt -eq 3){throw}; Start-Sleep -Seconds $attempt }
    }
}
$base='https://www2.ninjal.ac.jp/'
if($Bank -in @('all','verbs')) {
    Get-CachedFile ($base+'basicverbbank/js/single_verb_headwords.js') 'sources/ninjal-verb-headwords.js'
    $raw=Get-Content -LiteralPath (Join-Path $projectRoot 'sources/ninjal-verb-headwords.js') -Raw -Encoding utf8
    $index=($raw -replace '^var single_verb_headwords\s*=\s*','' -replace ';\s*$','') | ConvertFrom-Json -AsHashtable
    foreach($head in @($index.Values | ForEach-Object {$_})) {
        Get-CachedFile ($base+'basicverbbank/single_headwords/'+[uri]::EscapeDataString($head.headword_key)+'.html') ('sources/ninjal-verbs/'+$head.headword_key+'.html')
    }
}
if($Bank -in @('all','cases')) {
    foreach($stem in @('ga','wo','ni','he','de','kara','made','yori','to')) {
        $folder=$stem+'-kaku'
        $relative='sources/ninjal-cases/'+$folder+'_summary.json'
        Get-CachedFile ($base+'caseparticlebank/thematic_roles/'+$folder+'_summary.json') $relative
        $summary=Get-Content -LiteralPath (Join-Path $projectRoot $relative) -Raw -Encoding utf8 | ConvertFrom-Json
        foreach($role in $summary.roles) {
            Get-CachedFile ($base+'caseparticlebank/thematic_roles/'+$folder+'/'+[uri]::EscapeDataString($role.role)+'.json?v=20261022f') ('sources/ninjal-cases/'+$folder+'/'+$role.role+'.json')
        }
    }
}
Write-Output 'All indexed source files are cached. Run build_ninjal_banks.py to validate and build.'
