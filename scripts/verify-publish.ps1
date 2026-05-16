param(
    [string]$RepoRoot = '',
    [string]$VaultRoot = 'C:\Users\zkl\OneDrive\Obsdian\Obsidian',
    [string]$MappingPath = '',
    [string[]]$EntryId,
    [switch]$OnlyMigrateNow
)

. (Join-Path $PSScriptRoot 'nemo-skills-common.ps1')

if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }
if (-not $MappingPath) { $MappingPath = Join-Path (Join-Path $RepoRoot 'docs') 'mapping.json' }

$mapping = Read-NemoMapping -MappingPath $MappingPath
$entries = Get-NemoEntries -Mapping $mapping -EntryId $EntryId -OnlyMigrateNow:$OnlyMigrateNow
if (-not $entries -or @($entries).Count -eq 0) {
    throw 'No entries selected for verification.'
}

$results = New-Object System.Collections.Generic.List[object]
$failed = $false
foreach ($entry in $entries) {
    $destinationPath = Join-Path $VaultRoot $entry.destination
    $managedState = Get-NemoManagedState -Entry $entry -DestinationPath $destinationPath
    if ($managedState.state -ne 'managed') {
        $failed = $true
        $results.Add([pscustomobject]@{ entry_id = $entry.id; status = 'missing_or_unmanaged'; issues = @("destination state is $($managedState.state)") }) | Out-Null
        continue
    }
    $drift = Test-NemoEntryDrift -Entry $entry -RepoRoot $RepoRoot -VaultRoot $VaultRoot
    if (-not $drift.clean) {
        $failed = $true
        $results.Add([pscustomobject]@{ entry_id = $entry.id; status = 'drift'; issues = $drift.issues }) | Out-Null
        continue
    }
    $results.Add([pscustomobject]@{ entry_id = $entry.id; status = 'clean'; issues = @() }) | Out-Null
}

$results | ConvertTo-Json -Depth 10
if ($failed) { exit 1 }
exit 0
