param(
    [Parameter(Mandatory = $true)]
    [string]$BatchId,
    [string]$RepoRoot = '',
    [string]$VaultRoot = 'C:\Users\zkl\OneDrive\Obsdian\Obsidian',
    [string]$MappingPath = '',
    [string[]]$EntryId
)

. (Join-Path $PSScriptRoot 'nemo-skills-common.ps1')

if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }
if (-not $MappingPath) { $MappingPath = Join-Path (Join-Path $RepoRoot 'docs') 'mapping.json' }

$mapping = Read-NemoMapping -MappingPath $MappingPath
$entries = Get-NemoEntries -Mapping $mapping -EntryId $EntryId
if (-not $entries -or @($entries).Count -eq 0) {
    throw 'No entries selected for rollback.'
}
$backupRoot = Join-Path $VaultRoot ".agents/.nemo-backups/skills/$BatchId"
if (-not (Test-Path -LiteralPath $backupRoot)) {
    throw "Backup batch not found: $backupRoot"
}

$missingBackups = New-Object System.Collections.Generic.List[string]
foreach ($entry in $entries) {
    $destinationPath = Join-Path $VaultRoot $entry.destination
    $backupPath = if ($entry.type -eq 'skill_dir') {
        Join-Path $backupRoot $entry.destination
    }
    else {
        Join-Path $backupRoot (Join-Path 'files' (Split-Path -Leaf $destinationPath))
    }
    if (-not (Test-Path -LiteralPath $backupPath)) {
        $missingBackups.Add("$($entry.id): $backupPath") | Out-Null
    }
}
if ($missingBackups.Count -gt 0) {
    throw "Rollback preflight failed; missing backups: $($missingBackups -join '; ')"
}

$results = New-Object System.Collections.Generic.List[object]
foreach ($entry in $entries) {
    $destinationPath = Join-Path $VaultRoot $entry.destination
    $meta = Get-NemoMetaPaths -DestinationPath $destinationPath -Type $entry.type

    foreach ($path in @($destinationPath, $meta.marker, $meta.manifest)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }

    if ($entry.type -eq 'skill_dir') {
        $backupPath = Join-Path $backupRoot $entry.destination
        if (Test-Path -LiteralPath $backupPath) {
            Ensure-NemoParentDirectory -Path $destinationPath
            Move-Item -LiteralPath $backupPath -Destination $destinationPath -Force
        }
    }
    else {
        $backupFile = Join-Path $backupRoot (Join-Path 'files' (Split-Path -Leaf $destinationPath))
        if (Test-Path -LiteralPath $backupFile) {
            Ensure-NemoParentDirectory -Path $destinationPath
            Move-Item -LiteralPath $backupFile -Destination $destinationPath -Force
        }
    }

    $results.Add([pscustomobject]@{ entry_id = $entry.id; restored = (Test-Path -LiteralPath $destinationPath) }) | Out-Null
}

$results | ConvertTo-Json -Depth 10
exit 0
