Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-NemoMapping {
    param([string]$MappingPath)
    if (-not (Test-Path -LiteralPath $MappingPath)) {
        throw "Mapping file not found: $MappingPath"
    }
    return Get-Content -LiteralPath $MappingPath -Raw | ConvertFrom-Json
}

function Get-NemoEntries {
    param(
        $Mapping,
        [string[]]$EntryId,
        [switch]$OnlyMigrateNow
    )
    $entries = @($Mapping.entries)
    if ($OnlyMigrateNow) {
        $entries = @($entries | Where-Object { $_.status -eq 'migrate_now' })
    }
    if ($EntryId -and $EntryId.Count -gt 0) {
        $wanted = [System.Collections.Generic.HashSet[string]]::new([string[]]$EntryId, [System.StringComparer]::Ordinal)
        $entries = @($entries | Where-Object { $wanted.Contains([string]$_.id) })
    }
    return $entries
}

function ConvertTo-NemoRelativePath {
    param(
        [string]$Root,
        [string]$Path
    )
    $rootResolved = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\') + '\'
    $pathResolved = (Resolve-Path -LiteralPath $Path).Path
    $rootUri = New-Object System.Uri($rootResolved)
    $pathUri = New-Object System.Uri($pathResolved)
    $relative = $rootUri.MakeRelativeUri($pathUri).ToString()
    return [System.Uri]::UnescapeDataString($relative).Replace('\', '/')
}

function Get-NemoSortedPaths {
    param([string[]]$Paths)
    $array = @($Paths)
    [array]::Sort($array, [System.StringComparer]::Ordinal)
    return $array
}

function Get-NemoFileHashValue {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-NemoManifestData {
    param(
        [string]$Path,
        [ValidateSet('skill_dir','prompt_file')] [string]$Type,
        [string[]]$ExcludeRelativePath = @()
    )

    $excludeSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($exclude in $ExcludeRelativePath) {
        [void]$excludeSet.Add($exclude)
    }

    $files = @()
    if ($Type -eq 'skill_dir') {
        if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
            throw "Directory not found: $Path"
        }
        foreach ($file in Get-ChildItem -LiteralPath $Path -Recurse -File) {
            $relative = ConvertTo-NemoRelativePath -Root $Path -Path $file.FullName
            if ($excludeSet.Contains($relative)) {
                continue
            }
            $files += [pscustomobject]@{
                path = $relative
                sha256 = Get-NemoFileHashValue -Path $file.FullName
            }
        }
    }
    else {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            throw "File not found: $Path"
        }
        $name = [System.IO.Path]::GetFileName($Path)
        if (-not $excludeSet.Contains($name)) {
            $files += [pscustomobject]@{
                path = $name
                sha256 = Get-NemoFileHashValue -Path $Path
            }
        }
    }

    $normalized = foreach ($item in $files) { [pscustomobject]@{ path = [string]$item.path; sha256 = [string]$item.sha256 } }
    $orderedPaths = Get-NemoSortedPaths -Paths @($normalized | ForEach-Object { $_.path })
    $orderedFiles = foreach ($path in $orderedPaths) {
        $match = $normalized | Where-Object { $_.path -ceq $path } | Select-Object -First 1
        [pscustomobject]@{ path = $match.path; sha256 = $match.sha256 }
    }
    return [pscustomobject]@{
        generated_at = [DateTime]::UtcNow.ToString('o')
        files = $orderedFiles
        file_count = @($orderedFiles).Count
    }
}

function Get-NemoMetaPaths {
    param(
        [string]$DestinationPath,
        [ValidateSet('skill_dir','prompt_file')] [string]$Type
    )
    if ($Type -eq 'skill_dir') {
        return [pscustomobject]@{
            marker = Join-Path $DestinationPath '.nemo-managed.json'
            manifest = Join-Path $DestinationPath '.nemo-manifest.json'
            markerRelative = '.nemo-managed.json'
            manifestRelative = '.nemo-manifest.json'
        }
    }
    return [pscustomobject]@{
        marker = "$DestinationPath.nemo-managed.json"
        manifest = "$DestinationPath.nemo-manifest.json"
        markerRelative = ([System.IO.Path]::GetFileName("$DestinationPath.nemo-managed.json"))
        manifestRelative = ([System.IO.Path]::GetFileName("$DestinationPath.nemo-manifest.json"))
    }
}

function Write-NemoJson {
    param([string]$Path, $Data)
    $json = $Data | ConvertTo-Json -Depth 20
    Set-Content -LiteralPath $Path -Value ($json + [Environment]::NewLine) -Encoding UTF8
}

function Get-NemoManagedState {
    param(
        [pscustomobject]$Entry,
        [string]$DestinationPath
    )
    $meta = Get-NemoMetaPaths -DestinationPath $DestinationPath -Type $Entry.type
    $targetExists = Test-Path -LiteralPath $DestinationPath
    $markerExists = Test-Path -LiteralPath $meta.marker -PathType Leaf
    $manifestExists = Test-Path -LiteralPath $meta.manifest -PathType Leaf
    if (-not $targetExists) {
        return [pscustomobject]@{ state = 'missing'; meta = $meta }
    }
    if (-not $markerExists -or -not $manifestExists) {
        return [pscustomobject]@{ state = 'unmanaged'; meta = $meta }
    }
    $marker = Get-Content -LiteralPath $meta.marker -Raw | ConvertFrom-Json
    $managed = ($marker.managed_by -ceq 'nemo-skills') -and ($marker.entry_id -ceq $Entry.id)
    if (-not $managed) {
        return [pscustomobject]@{ state = 'unmanaged'; meta = $meta; marker = $marker }
    }
    return [pscustomobject]@{ state = 'managed'; meta = $meta; marker = $marker }
}

function Compare-NemoManifest {
    param(
        [pscustomobject]$Expected,
        [pscustomobject]$Actual
    )
    $issues = New-Object System.Collections.Generic.List[string]
    if ($Expected.file_count -ne $Actual.file_count) {
        $issues.Add("file_count mismatch expected=$($Expected.file_count) actual=$($Actual.file_count)") | Out-Null
    }
    $expectedPaths = @($Expected.files | ForEach-Object { $_.path })
    $actualPaths = @($Actual.files | ForEach-Object { $_.path })
    if (@($expectedPaths).Count -ne @($actualPaths).Count -or (Compare-Object -ReferenceObject $expectedPaths -DifferenceObject $actualPaths -SyncWindow 0)) {
        $issues.Add('path set mismatch') | Out-Null
    }
    $actualMap = @{}
    foreach ($file in $Actual.files) {
        $actualMap[[string]$file.path] = [string]$file.sha256
    }
    foreach ($file in $Expected.files) {
        $path = [string]$file.path
        if (-not $actualMap.ContainsKey($path)) {
            $issues.Add("missing file: $path") | Out-Null
            continue
        }
        if ($actualMap[$path] -cne [string]$file.sha256) {
            $issues.Add("hash mismatch: $path") | Out-Null
        }
    }
    return [pscustomobject]@{
        clean = ($issues.Count -eq 0)
        issues = @($issues)
    }
}

function Test-NemoEntryDrift {
    param(
        [pscustomobject]$Entry,
        [string]$RepoRoot,
        [string]$VaultRoot
    )
    $sourcePath = Join-Path $RepoRoot $Entry.source
    $destinationPath = Join-Path $VaultRoot $Entry.destination
    $managedState = Get-NemoManagedState -Entry $Entry -DestinationPath $destinationPath
    if ($managedState.state -ne 'managed') {
        return [pscustomobject]@{ clean = $false; reason = $managedState.state; issues = @("destination state is $($managedState.state)") }
    }
    $meta = $managedState.meta
    $exclude = @($meta.markerRelative, $meta.manifestRelative)
    $expected = Get-NemoManifestData -Path $sourcePath -Type $Entry.type
    $actual = if ($Entry.type -eq 'skill_dir') {
        Get-NemoManifestData -Path $destinationPath -Type $Entry.type -ExcludeRelativePath $exclude
    } else {
        Get-NemoManifestData -Path $destinationPath -Type $Entry.type
    }
    $comparison = Compare-NemoManifest -Expected $expected -Actual $actual
    return [pscustomobject]@{
        clean = $comparison.clean
        reason = if ($comparison.clean) { 'clean' } else { 'drift' }
        issues = $comparison.issues
        expected = $expected
        actual = $actual
        meta = $meta
    }
}

function New-NemoManagedMarker {
    param(
        [pscustomobject]$Entry,
        [string]$BatchId,
        [string]$Warning,
        [string]$ManifestFileName
    )
    return [pscustomobject]@{
        managed_by = 'nemo-skills'
        entry_id = $Entry.id
        type = $Entry.type
        source = $Entry.source
        published_at = [DateTime]::UtcNow.ToString('o')
        batch = $BatchId
        manifest_file = $ManifestFileName
        warning = $Warning
    }
}

function Ensure-NemoParentDirectory {
    param([string]$Path)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
}

