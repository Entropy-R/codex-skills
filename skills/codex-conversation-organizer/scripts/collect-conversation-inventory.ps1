[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$CodexHome,

    [string[]]$SourceProjectIds = @(),

    [switch]$IncludeArchived,

    [ValidateRange(0, 2000)]
    [int]$MaxPreviewCharacters = 0,

    [string]$UpdatedAfter,

    [string]$UpdatedBefore,

    [ValidateRange(0, 100000)]
    [int]$MaxConversations = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-NamedPropertyValue {
    param(
        [AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function Get-FirstNamedPropertyValue {
    param(
        [AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    foreach ($name in $Names) {
        $value = Get-NamedPropertyValue -Object $Object -Name $name
        if ($null -ne $value -and [string]$value -ne '') {
            return $value
        }
    }

    return $null
}

function Get-ProjectPath {
    param([AllowNull()][object]$Project)

    $path = Get-FirstNamedPropertyValue -Object $Project -Names @('path', 'workspaceRoot', 'remotePath')
    if (-not [string]::IsNullOrWhiteSpace([string]$path)) {
        return [string]$path
    }

    $rootPaths = @(Get-NamedPropertyValue -Object $Project -Name 'rootPaths')
    if ($rootPaths.Count -gt 0) {
        return [string]$rootPaths[0]
    }

    return $null
}

function ConvertTo-ProjectRows {
    param(
        [AllowNull()][object]$Projects,
        [Parameter(Mandatory = $true)][string]$ProjectKind
    )

    $rows = @()
    if ($null -eq $Projects) {
        return $rows
    }

    if ($Projects -is [System.Array] -or $Projects -is [System.Collections.IList]) {
        foreach ($value in @($Projects)) {
            $projectId = Get-FirstNamedPropertyValue -Object $value -Names @('projectId', 'id')
            if ($null -eq $projectId) {
                continue
            }
            $resolvedProjectKind = Get-FirstNamedPropertyValue -Object $value -Names @('projectKind', 'kind')
            if ([string]::IsNullOrWhiteSpace([string]$resolvedProjectKind)) {
                $resolvedProjectKind = $ProjectKind
            }
            $rows += [PSCustomObject]@{
                projectId   = [string]$projectId
                projectKind = [string]$resolvedProjectKind
                label       = [string](Get-FirstNamedPropertyValue -Object $value -Names @('label', 'name'))
                path        = [string](Get-ProjectPath -Project $value)
            }
        }
        return $rows
    }

    if ($Projects -is [System.Collections.IDictionary]) {
        foreach ($entry in $Projects.GetEnumerator()) {
            $value = $entry.Value
            $rows += [PSCustomObject]@{
                projectId   = [string]$entry.Key
                projectKind = $ProjectKind
                label       = [string](Get-FirstNamedPropertyValue -Object $value -Names @('label', 'name'))
                path        = [string](Get-ProjectPath -Project $value)
            }
        }
        return $rows
    }

    $properties = @($Projects.PSObject.Properties)
    $looksLikeMap = $properties.Count -gt 0 -and
        $properties.Name -notcontains 'projectId' -and
        $properties.Name -notcontains 'id'

    if ($looksLikeMap) {
        foreach ($property in $properties) {
            $value = $property.Value
            $rows += [PSCustomObject]@{
                projectId   = [string]$property.Name
                projectKind = $ProjectKind
                label       = [string](Get-FirstNamedPropertyValue -Object $value -Names @('label', 'name'))
                path        = [string](Get-ProjectPath -Project $value)
            }
        }
        return $rows
    }

    foreach ($value in @($Projects)) {
        $projectId = Get-FirstNamedPropertyValue -Object $value -Names @('projectId', 'id')
        if ($null -eq $projectId) {
            continue
        }
        $resolvedProjectKind = Get-FirstNamedPropertyValue -Object $value -Names @('projectKind', 'kind')
        if ([string]::IsNullOrWhiteSpace([string]$resolvedProjectKind)) {
            $resolvedProjectKind = $ProjectKind
        }
        $rows += [PSCustomObject]@{
            projectId   = [string]$projectId
            projectKind = [string]$resolvedProjectKind
            label       = [string](Get-FirstNamedPropertyValue -Object $value -Names @('label', 'name'))
            path        = [string](Get-ProjectPath -Project $value)
        }
    }

    return $rows
}

if ([string]::IsNullOrWhiteSpace($CodexHome)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $CodexHome = $env:CODEX_HOME
    }
    else {
        $CodexHome = Join-Path $env:USERPROFILE '.codex'
    }
}

$resolvedCodexHome = [System.IO.Path]::GetFullPath($CodexHome)
$globalStatePath = Join-Path $resolvedCodexHome '.codex-global-state.json'
$databasePath = Join-Path $resolvedCodexHome 'state_5.sqlite'

if (-not (Test-Path -LiteralPath $globalStatePath -PathType Leaf)) {
    throw "Codex global state was not found: $globalStatePath"
}
if (-not (Test-Path -LiteralPath $databasePath -PathType Leaf)) {
    throw "Codex thread database was not found: $databasePath"
}

$sqliteCommand = Get-Command sqlite3.exe -ErrorAction SilentlyContinue
if ($null -eq $sqliteCommand) {
    $sqliteCommand = Get-Command sqlite3 -ErrorAction SilentlyContinue
}
if ($null -eq $sqliteCommand) {
    throw 'sqlite3 is required for complete local inventory. Install it or use the Codex app thread tools for a bounded inventory.'
}

$globalState = Get-Content -Raw -LiteralPath $globalStatePath -Encoding UTF8 | ConvertFrom-Json
$assignmentsObject = Get-NamedPropertyValue -Object $globalState -Name 'thread-project-assignments'
$assignmentMap = @{}
if ($null -ne $assignmentsObject) {
    foreach ($property in @($assignmentsObject.PSObject.Properties)) {
        $assignmentMap[[string]$property.Name] = $property.Value
    }
}

$projectlessSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($threadId in @(Get-NamedPropertyValue -Object $globalState -Name 'projectless-thread-ids')) {
    if (-not [string]::IsNullOrWhiteSpace([string]$threadId)) {
        [void]$projectlessSet.Add([string]$threadId)
    }
}

$projects = @()
$projects += ConvertTo-ProjectRows -Projects (Get-NamedPropertyValue -Object $globalState -Name 'local-projects') -ProjectKind 'local'
$projects += ConvertTo-ProjectRows -Projects (Get-NamedPropertyValue -Object $globalState -Name 'remote-projects') -ProjectKind 'remote'

$sql = @"
SELECT
    id,
    cwd,
    title,
    preview,
    archived,
    COALESCE(created_at_ms, created_at * 1000) AS created_at_ms,
    COALESCE(updated_at_ms, updated_at * 1000) AS updated_at_ms,
    source,
    COALESCE(thread_source, '') AS thread_source,
    COALESCE(agent_role, '') AS agent_role,
    COALESCE(git_branch, '') AS git_branch,
    COALESCE(git_origin_url, '') AS git_origin_url
FROM threads
WHERE COALESCE(thread_source, '') <> 'subagent'
  AND COALESCE(agent_role, '') = ''
  AND source NOT LIKE '%"subagent"%'
ORDER BY COALESCE(updated_at_ms, updated_at * 1000) DESC;
"@

$databaseUri = 'file:' + ($databasePath -replace '\\', '/') + '?mode=ro'
$rawRows = & $sqliteCommand.Source '-json' $databaseUri $sql
if ($LASTEXITCODE -ne 0) {
    throw "sqlite3 inventory query failed with exit code $LASTEXITCODE."
}

$rows = @()
if (-not [string]::IsNullOrWhiteSpace(($rawRows -join "`n"))) {
    $rows = @(($rawRows -join "`n") | ConvertFrom-Json)
}

$sourceProjectSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($projectId in $SourceProjectIds) {
    if (-not [string]::IsNullOrWhiteSpace($projectId)) {
        [void]$sourceProjectSet.Add($projectId)
    }
}

$updatedAfterMs = $null
if (-not [string]::IsNullOrWhiteSpace($UpdatedAfter)) {
    $parsedUpdatedAfter = [DateTimeOffset]::Parse($UpdatedAfter)
    $updatedAfterMs = $parsedUpdatedAfter.ToUnixTimeMilliseconds()
}

$updatedBeforeMs = $null
if (-not [string]::IsNullOrWhiteSpace($UpdatedBefore)) {
    $parsedUpdatedBefore = [DateTimeOffset]::Parse($UpdatedBefore)
    $updatedBeforeMs = $parsedUpdatedBefore.ToUnixTimeMilliseconds()
}

$conversations = @()
$truncated = $false
foreach ($row in $rows) {
    if (-not $IncludeArchived -and [int]$row.archived -ne 0) {
        continue
    }

    $assignment = $null
    if ($assignmentMap.ContainsKey([string]$row.id)) {
        $assignmentValue = $assignmentMap[[string]$row.id]
        if ($assignmentValue -is [string]) {
            $assignment = [PSCustomObject]@{
                projectKind = 'local'
                projectId   = [string]$assignmentValue
            }
        }
        else {
            $assignment = [PSCustomObject]@{
                projectKind = [string](Get-NamedPropertyValue -Object $assignmentValue -Name 'projectKind')
                projectId   = [string](Get-NamedPropertyValue -Object $assignmentValue -Name 'projectId')
            }
        }
    }

    $currentProjectId = if ($null -eq $assignment) { $null } else { $assignment.projectId }
    if ($sourceProjectSet.Count -gt 0 -and -not $sourceProjectSet.Contains([string]$currentProjectId)) {
        continue
    }

    $rowUpdatedAtMs = [long]$row.updated_at_ms
    if ($null -ne $updatedAfterMs -and $rowUpdatedAtMs -lt $updatedAfterMs) {
        continue
    }
    if ($null -ne $updatedBeforeMs -and $rowUpdatedAtMs -gt $updatedBeforeMs) {
        continue
    }
    if ($MaxConversations -gt 0 -and $conversations.Count -ge $MaxConversations) {
        $truncated = $true
        break
    }

    $preview = [string]$row.preview
    if ($MaxPreviewCharacters -eq 0) {
        $preview = ''
    }
    elseif ($preview.Length -gt $MaxPreviewCharacters) {
        $preview = $preview.Substring(0, $MaxPreviewCharacters)
    }

    $conversations += [PSCustomObject]@{
        threadId         = [string]$row.id
        title            = [string]$row.title
        preview          = $preview
        currentAssignment = $assignment
        isProjectless    = $projectlessSet.Contains([string]$row.id)
        archived         = [bool]([int]$row.archived)
        createdAtMs      = [long]$row.created_at_ms
        updatedAtMs      = $rowUpdatedAtMs
        cwd              = [string]$row.cwd
        gitBranch        = [string]$row.git_branch
        gitOriginUrl     = [string]$row.git_origin_url
    }
}

$inventory = [PSCustomObject]@{
    schemaVersion = 1
    generatedAt   = [DateTimeOffset]::UtcNow.ToString('o')
    source         = 'local-codex-state-read-only'
    scope          = [PSCustomObject]@{
        sourceProjectIds = @($SourceProjectIds)
        includeArchived  = [bool]$IncludeArchived
        updatedAfter     = if ([string]::IsNullOrWhiteSpace($UpdatedAfter)) { $null } else { $UpdatedAfter }
        updatedBefore    = if ([string]::IsNullOrWhiteSpace($UpdatedBefore)) { $null } else { $UpdatedBefore }
        maxConversations = $MaxConversations
    }
    truncated      = $truncated
    projects       = @($projects | Sort-Object projectKind, projectId)
    conversations  = $conversations
}

$resolvedOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $resolvedOutputPath
if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    [void](New-Item -ItemType Directory -Path $outputDirectory -Force)
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$json = $inventory | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($resolvedOutputPath, $json, $utf8NoBom)

[PSCustomObject]@{
    outputPath        = $resolvedOutputPath
    projectCount      = @($projects).Count
    conversationCount = @($conversations).Count
    truncated         = $truncated
}
