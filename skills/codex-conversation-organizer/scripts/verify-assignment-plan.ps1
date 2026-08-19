[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath,

    [string]$StatePath,

    [string]$CodexHome,

    [string]$OutputPath,

    [switch]$FailOnMismatch
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

function Get-AssignmentValue {
    param(
        [AllowNull()][object]$Assignments,
        [Parameter(Mandatory = $true)][string]$ThreadId
    )

    if ($null -eq $Assignments) {
        return $null
    }
    $property = $Assignments.PSObject.Properties[$ThreadId]
    if ($null -eq $property) {
        return $null
    }

    $value = $property.Value
    if ($value -is [string]) {
        return [PSCustomObject]@{
            projectKind = 'local'
            projectId   = [string]$value
        }
    }

    return [PSCustomObject]@{
        projectKind = [string](Get-NamedPropertyValue -Object $value -Name 'projectKind')
        projectId   = [string](Get-NamedPropertyValue -Object $value -Name 'projectId')
    }
}

function Test-AssignmentsEqual {
    param(
        [AllowNull()][object]$Expected,
        [AllowNull()][object]$Actual
    )

    if ($null -eq $Expected -and $null -eq $Actual) {
        return $true
    }
    if ($null -eq $Expected -or $null -eq $Actual) {
        return $false
    }

    $expectedKind = [string](Get-NamedPropertyValue -Object $Expected -Name 'projectKind')
    $expectedId = [string](Get-NamedPropertyValue -Object $Expected -Name 'projectId')
    $actualKind = [string](Get-NamedPropertyValue -Object $Actual -Name 'projectKind')
    $actualId = [string](Get-NamedPropertyValue -Object $Actual -Name 'projectId')
    return $expectedKind -ceq $actualKind -and $expectedId -ceq $actualId
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 20), $utf8NoBom)
}

if ([string]::IsNullOrWhiteSpace($CodexHome)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $CodexHome = $env:CODEX_HOME
    }
    else {
        $CodexHome = Join-Path $env:USERPROFILE '.codex'
    }
}
if ([string]::IsNullOrWhiteSpace($StatePath)) {
    $StatePath = Join-Path $CodexHome '.codex-global-state.json'
}

$resolvedPlanPath = [System.IO.Path]::GetFullPath($PlanPath)
$resolvedStatePath = [System.IO.Path]::GetFullPath($StatePath)
if (-not (Test-Path -LiteralPath $resolvedPlanPath -PathType Leaf)) {
    throw "Migration plan was not found: $resolvedPlanPath"
}
if (-not (Test-Path -LiteralPath $resolvedStatePath -PathType Leaf)) {
    throw "Codex state was not found: $resolvedStatePath"
}

$plan = Get-Content -Raw -LiteralPath $resolvedPlanPath -Encoding UTF8 | ConvertFrom-Json
$state = Get-Content -Raw -LiteralPath $resolvedStatePath -Encoding UTF8 | ConvertFrom-Json
if ([int](Get-NamedPropertyValue -Object $plan -Name 'schemaVersion') -ne 1) {
    throw 'Unsupported migration plan schemaVersion. Expected 1.'
}

$assignments = Get-NamedPropertyValue -Object $state -Name 'thread-project-assignments'
if ($null -eq $assignments) {
    throw 'Current state does not contain thread-project-assignments.'
}

$projectlessIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($threadId in @(Get-NamedPropertyValue -Object $state -Name 'projectless-thread-ids')) {
    if (-not [string]::IsNullOrWhiteSpace([string]$threadId)) {
        [void]$projectlessIds.Add([string]$threadId)
    }
}

$details = @()
foreach ($operation in @($plan.operations)) {
    $threadId = [string]$operation.threadId
    $actualAssignment = Get-AssignmentValue -Assignments $assignments -ThreadId $threadId
    $assignmentMatches = Test-AssignmentsEqual -Expected $operation.targetAssignment -Actual $actualAssignment
    $stillProjectless = $projectlessIds.Contains($threadId)

    $details += [PSCustomObject]@{
        threadId          = $threadId
        expectedProjectId = [string]$operation.targetAssignment.projectId
        actualProjectId   = if ($null -eq $actualAssignment) { $null } else { [string]$actualAssignment.projectId }
        assignmentMatches = $assignmentMatches
        stillProjectless  = $stillProjectless
        verified          = $assignmentMatches -and -not $stillProjectless
    }
}

$mismatches = @($details | Where-Object { -not $_.verified })
$result = [PSCustomObject]@{
    schemaVersion  = 1
    verifiedAt     = [DateTimeOffset]::UtcNow.ToString('o')
    planId         = [string]$plan.planId
    statePath      = $resolvedStatePath
    status         = if ($mismatches.Count -eq 0) { 'verified' } else { 'deviations' }
    operationCount = $details.Count
    verifiedCount  = $details.Count - $mismatches.Count
    mismatchCount  = $mismatches.Count
    details        = $details
}

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $resolvedOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = Split-Path -Parent $resolvedOutputPath
    if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
        [void](New-Item -ItemType Directory -Path $outputDirectory -Force)
    }
    Write-JsonFile -Value $result -Path $resolvedOutputPath
}

$result
if ($FailOnMismatch -and $mismatches.Count -gt 0) {
    throw "$($mismatches.Count) reassignment operation(s) did not verify."
}
