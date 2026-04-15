param(
    [string]$RepoRoot = '',
    [string]$VaultRoot = 'C:\Users\zkl\OneDrive\Obsdian\Obsidian',
    [string]$MappingPath = '',
    [string[]]$EntryId,
    [ValidateSet('FailOnConflict','OverwriteManagedClean','ForceManagedDrift','ForceUnmanaged')]
    [string]$Mode = 'FailOnConflict',
    [string]$BatchId = ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')),
    [switch]$OnlyMigrateNow,
    [switch]$DryRun
)

. (Join-Path $PSScriptRoot 'nemo-skills-common.ps1')

if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }
if (-not $MappingPath) { $MappingPath = Join-Path (Join-Path $RepoRoot 'docs') 'mapping.json' }

$mapping = Read-NemoMapping -MappingPath $MappingPath
$entries = Get-NemoEntries -Mapping $mapping -EntryId $EntryId -OnlyMigrateNow:$OnlyMigrateNow
if (-not $entries -or @($entries).Count -eq 0) {
    throw 'No entries selected for publish.'
}

$backupRoot = Join-Path $VaultRoot ".skills/.nemo-backups/$BatchId"
$warning = 'Managed by nemo-skills. Do not edit here; edit the nemo-skills repo and republish.'
$results = New-Object System.Collections.Generic.List[object]

foreach ($entry in $entries) {
    $sourcePath = Join-Path $RepoRoot $entry.source
    $destinationPath = Join-Path $VaultRoot $entry.destination
    $destParent = Split-Path -Parent $destinationPath
    Ensure-NemoParentDirectory -Path $destinationPath

    $managedState = Get-NemoManagedState -Entry $entry -DestinationPath $destinationPath
    if ($managedState.state -eq 'managed') {
        $drift = Test-NemoEntryDrift -Entry $entry -RepoRoot $RepoRoot -VaultRoot $VaultRoot
        $managedState | Add-Member -NotePropertyName drift -NotePropertyValue $drift -Force
    }

    $skipPublish = $false

    switch ($managedState.state) {
        'missing' { }
        'unmanaged' {
            if ($Mode -ne 'ForceUnmanaged') {
                throw "Unmanaged target exists for $($entry.id). Re-run with -Mode ForceUnmanaged after review."
            }
        }
        'managed' {
            if ($managedState.drift.clean) {
                if ($Mode -eq 'FailOnConflict') {
                    $results.Add([pscustomobject]@{
                        entry_id = $entry.id
                        destination = $entry.destination
                        state_before = $managedState.state
                        mode = $Mode
                        batch = $BatchId
                        dry_run = [bool]$DryRun
                        skipped = 'managed_clean_noop'
                    }) | Out-Null
                    $skipPublish = $true
                }
                elseif ($Mode -ne 'OverwriteManagedClean') {
                    throw "Managed clean target exists for $($entry.id). Re-run with -Mode OverwriteManagedClean to replace it."
                }
            }
            else {
                if ($Mode -ne 'ForceManagedDrift') {
                    throw "Managed drift detected for $($entry.id). Re-run with -Mode ForceManagedDrift after review."
                }
            }
        }
        default {
            throw "Unsupported target state for $($entry.id): $($managedState.state)"
        }
    }

    if ($skipPublish) {
        continue
    }

    $stageLeaf = ".nemo-stage-$($entry.id)-$BatchId"
    if ($entry.type -eq 'skill_dir') {
        $stagePath = Join-Path $destParent $stageLeaf
        if (Test-Path -LiteralPath $stagePath) {
            Remove-Item -LiteralPath $stagePath -Recurse -Force
        }
        if (-not $DryRun) {
            Copy-Item -LiteralPath $sourcePath -Destination $stagePath -Recurse -Force
        }
        $stageMeta = Get-NemoMetaPaths -DestinationPath $stagePath -Type $entry.type
        $manifest = Get-NemoManifestData -Path $sourcePath -Type $entry.type
        $marker = New-NemoManagedMarker -Entry $entry -BatchId $BatchId -Warning $warning -ManifestFileName $stageMeta.manifestRelative
        if (-not $DryRun) {
            Write-NemoJson -Path $stageMeta.marker -Data $marker
            Write-NemoJson -Path $stageMeta.manifest -Data $manifest
        }

        if (-not $DryRun) {
            $stageActual = Get-NemoManifestData -Path $stagePath -Type $entry.type -ExcludeRelativePath @($stageMeta.markerRelative, $stageMeta.manifestRelative)
            $stageComparison = Compare-NemoManifest -Expected $manifest -Actual $stageActual
            if (-not $stageComparison.clean) {
                throw "Stage verification failed for $($entry.id): $($stageComparison.issues -join '; ')"
            }
        }

        if (Test-Path -LiteralPath $destinationPath) {
            $backupPath = Join-Path $backupRoot $entry.destination
            Ensure-NemoParentDirectory -Path $backupPath
            if (-not $DryRun) {
                Move-Item -LiteralPath $destinationPath -Destination $backupPath -Force
            }
            $meta = Get-NemoMetaPaths -DestinationPath $destinationPath -Type $entry.type
            foreach ($path in @($meta.marker, $meta.manifest)) {
                if (Test-Path -LiteralPath $path) {
                    $backupMetaPath = Join-Path $backupRoot ((ConvertTo-NemoRelativePath -Root $VaultRoot -Path $path))
                    Ensure-NemoParentDirectory -Path $backupMetaPath
                    if (-not $DryRun) {
                        Move-Item -LiteralPath $path -Destination $backupMetaPath -Force
                    }
                }
            }
        }

        if (-not $DryRun) {
            Move-Item -LiteralPath $stagePath -Destination $destinationPath -Force
        }
    }
    else {
        $stageDir = Join-Path $destParent $stageLeaf
        if (Test-Path -LiteralPath $stageDir) {
            Remove-Item -LiteralPath $stageDir -Recurse -Force
        }
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $stageDir -Force | Out-Null
        }
        $targetLeaf = Split-Path -Leaf $destinationPath
        $stageFile = Join-Path $stageDir $targetLeaf
        if (-not $DryRun) {
            Copy-Item -LiteralPath $sourcePath -Destination $stageFile -Force
        }
        $stageMeta = Get-NemoMetaPaths -DestinationPath $stageFile -Type $entry.type
        $manifest = Get-NemoManifestData -Path $sourcePath -Type $entry.type
        $marker = New-NemoManagedMarker -Entry $entry -BatchId $BatchId -Warning $warning -ManifestFileName ([System.IO.Path]::GetFileName($stageMeta.manifest))
        if (-not $DryRun) {
            Write-NemoJson -Path $stageMeta.marker -Data $marker
            Write-NemoJson -Path $stageMeta.manifest -Data $manifest
        }

        if (Test-Path -LiteralPath $destinationPath) {
            $backupPath = Join-Path $backupRoot (Join-Path 'files' (Split-Path -Leaf $destinationPath))
            Ensure-NemoParentDirectory -Path $backupPath
            if (-not $DryRun) {
                Move-Item -LiteralPath $destinationPath -Destination $backupPath -Force
            }
            $meta = Get-NemoMetaPaths -DestinationPath $destinationPath -Type $entry.type
            foreach ($path in @($meta.marker, $meta.manifest)) {
                if (Test-Path -LiteralPath $path) {
                    $backupMetaPath = Join-Path $backupRoot (Join-Path 'files' (Split-Path -Leaf $path))
                    Ensure-NemoParentDirectory -Path $backupMetaPath
                    if (-not $DryRun) {
                        Move-Item -LiteralPath $path -Destination $backupMetaPath -Force
                    }
                }
            }
        }

        if (-not $DryRun) {
            Move-Item -LiteralPath $stageFile -Destination $destinationPath -Force
            Move-Item -LiteralPath $stageMeta.marker -Destination "$destinationPath.nemo-managed.json" -Force
            Move-Item -LiteralPath $stageMeta.manifest -Destination "$destinationPath.nemo-manifest.json" -Force
            Remove-Item -LiteralPath $stageDir -Force
        }
    }

    $results.Add([pscustomobject]@{
        entry_id = $entry.id
        destination = $entry.destination
        state_before = $managedState.state
        mode = $Mode
        batch = $BatchId
        dry_run = [bool]$DryRun
    }) | Out-Null
}

$results | ConvertTo-Json -Depth 10
exit 0

