[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath,

    [string]$StatePath,

    [string]$CodexHome,

    [string]$ThreadDatabasePath
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

function Add-ProjectIds {
    param(
        [AllowNull()][object]$Projects,
        [System.Collections.Generic.HashSet[string]]$Destination
    )

    if ($null -eq $Projects) {
        return
    }

    if ($Projects -is [System.Array] -or $Projects -is [System.Collections.IList]) {
        foreach ($project in @($Projects)) {
            $projectId = Get-NamedPropertyValue -Object $project -Name 'projectId'
            if ([string]::IsNullOrWhiteSpace([string]$projectId)) {
                $projectId = Get-NamedPropertyValue -Object $project -Name 'id'
            }
            if (-not [string]::IsNullOrWhiteSpace([string]$projectId)) {
                [void]$Destination.Add([string]$projectId)
            }
        }
        return
    }

    if ($Projects -is [System.Collections.IDictionary]) {
        foreach ($entry in $Projects.GetEnumerator()) {
            [void]$Destination.Add([string]$entry.Key)
        }
        return
    }

    $properties = @($Projects.PSObject.Properties)
    $looksLikeMap = $properties.Count -gt 0 -and
        $properties.Name -notcontains 'projectId' -and
        $properties.Name -notcontains 'id'

    if ($looksLikeMap) {
        foreach ($property in $properties) {
            [void]$Destination.Add([string]$property.Name)
        }
        return
    }

    foreach ($project in @($Projects)) {
        $projectId = Get-NamedPropertyValue -Object $project -Name 'projectId'
        if ([string]::IsNullOrWhiteSpace([string]$projectId)) {
            $projectId = Get-NamedPropertyValue -Object $project -Name 'id'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$projectId)) {
            [void]$Destination.Add([string]$projectId)
        }
    }
}

function Assert-NonEmptyText {
    param(
        [AllowNull()][object]$Value,
        [Parameter(Mandatory = $true)][string]$FieldName
    )

    if ([string]::IsNullOrWhiteSpace([string]$Value)) {
        throw "Required field is empty: $FieldName"
    }
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
if ([string]::IsNullOrWhiteSpace($ThreadDatabasePath)) {
    $defaultThreadDatabasePath = Join-Path $CodexHome 'state_5.sqlite'
    if (Test-Path -LiteralPath $defaultThreadDatabasePath -PathType Leaf) {
        $ThreadDatabasePath = $defaultThreadDatabasePath
    }
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

$knownThreadIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
if (-not [string]::IsNullOrWhiteSpace($ThreadDatabasePath)) {
    $resolvedThreadDatabasePath = [System.IO.Path]::GetFullPath($ThreadDatabasePath)
    if (-not (Test-Path -LiteralPath $resolvedThreadDatabasePath -PathType Leaf)) {
        throw "Codex thread database was not found: $resolvedThreadDatabasePath"
    }
    $sqliteCommand = Get-Command sqlite3.exe -ErrorAction SilentlyContinue
    if ($null -eq $sqliteCommand) {
        $sqliteCommand = Get-Command sqlite3 -ErrorAction SilentlyContinue
    }
    if ($null -eq $sqliteCommand) {
        throw 'sqlite3 is required to validate legacy threads that have no global assignment record.'
    }
    $databaseUri = 'file:' + ($resolvedThreadDatabasePath -replace '\\', '/') + '?mode=ro'
    $rawThreadRows = & $sqliteCommand.Source '-json' $databaseUri 'SELECT id FROM threads;'
    if ($LASTEXITCODE -ne 0) {
        throw "sqlite3 thread lookup failed with exit code $LASTEXITCODE."
    }
    if (-not [string]::IsNullOrWhiteSpace(($rawThreadRows -join "`n"))) {
        foreach ($threadRow in @((($rawThreadRows -join "`n") | ConvertFrom-Json))) {
            if (-not [string]::IsNullOrWhiteSpace([string]$threadRow.id)) {
                [void]$knownThreadIds.Add([string]$threadRow.id)
            }
        }
    }
}

if ([int](Get-NamedPropertyValue -Object $plan -Name 'schemaVersion') -ne 1) {
    throw 'Unsupported migration plan schemaVersion. Expected 1.'
}
Assert-NonEmptyText -Value (Get-NamedPropertyValue -Object $plan -Name 'planId') -FieldName 'planId'

$classificationPolicy = Get-NamedPropertyValue -Object $plan -Name 'classificationPolicy'
Assert-NonEmptyText -Value (Get-NamedPropertyValue -Object $classificationPolicy -Name 'originalUserText') -FieldName 'classificationPolicy.originalUserText'

$approval = Get-NamedPropertyValue -Object $plan -Name 'approval'
$approvalConfirmed = Get-NamedPropertyValue -Object $approval -Name 'confirmed'
if ($approvalConfirmed -isnot [bool] -or -not $approvalConfirmed) {
    throw 'The plan is not explicitly confirmed at approval.confirmed.'
}
Assert-NonEmptyText -Value (Get-NamedPropertyValue -Object $approval -Name 'confirmedAt') -FieldName 'approval.confirmedAt'

$assignments = Get-NamedPropertyValue -Object $state -Name 'thread-project-assignments'
if ($null -eq $assignments) {
    throw 'Current state does not contain thread-project-assignments.'
}

$projectIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
Add-ProjectIds -Projects (Get-NamedPropertyValue -Object $state -Name 'local-projects') -Destination $projectIds
Add-ProjectIds -Projects (Get-NamedPropertyValue -Object $state -Name 'remote-projects') -Destination $projectIds
if ($projectIds.Count -eq 0) {
    throw 'No saved projects were found in current state.'
}

$projectlessIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($threadId in @(Get-NamedPropertyValue -Object $state -Name 'projectless-thread-ids')) {
    if (-not [string]::IsNullOrWhiteSpace([string]$threadId)) {
        [void]$projectlessIds.Add([string]$threadId)
    }
}

$operations = @(Get-NamedPropertyValue -Object $plan -Name 'operations')
if ($operations.Count -eq 0) {
    throw 'The migration plan contains no operations.'
}

$seenThreadIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$validatedOperations = @()
foreach ($operation in $operations) {
    $threadId = [string](Get-NamedPropertyValue -Object $operation -Name 'threadId')
    Assert-NonEmptyText -Value $threadId -FieldName 'operations[].threadId'
    if (-not $seenThreadIds.Add($threadId)) {
        throw "Duplicate threadId in migration plan: $threadId"
    }

    $action = [string](Get-NamedPropertyValue -Object $operation -Name 'action')
    if ($action -cne 'reassign') {
        throw "Unsupported operation action '$action' for thread $threadId. Offline plans accept reassign only."
    }

    $operationApproved = Get-NamedPropertyValue -Object $operation -Name 'approved'
    if ($operationApproved -isnot [bool] -or -not $operationApproved) {
        throw "Operation is not individually approved: $threadId"
    }

    $classification = Get-NamedPropertyValue -Object $operation -Name 'classification'
    Assert-NonEmptyText -Value (Get-NamedPropertyValue -Object $classification -Name 'reason') -FieldName "operations[$threadId].classification.reason"

    $expectedAssignment = Get-NamedPropertyValue -Object $operation -Name 'currentAssignment'
    if ($null -ne $expectedAssignment) {
        Assert-NonEmptyText -Value (Get-NamedPropertyValue -Object $expectedAssignment -Name 'projectKind') -FieldName "operations[$threadId].currentAssignment.projectKind"
        Assert-NonEmptyText -Value (Get-NamedPropertyValue -Object $expectedAssignment -Name 'projectId') -FieldName "operations[$threadId].currentAssignment.projectId"
    }

    $targetAssignment = Get-NamedPropertyValue -Object $operation -Name 'targetAssignment'
    if ($null -eq $targetAssignment) {
        throw "Missing targetAssignment for thread $threadId."
    }
    $targetKind = [string](Get-NamedPropertyValue -Object $targetAssignment -Name 'projectKind')
    $targetProjectId = [string](Get-NamedPropertyValue -Object $targetAssignment -Name 'projectId')
    if ($targetKind -notin @('local', 'remote')) {
        throw "Unsupported target projectKind '$targetKind' for thread $threadId."
    }
    Assert-NonEmptyText -Value $targetProjectId -FieldName "operations[$threadId].targetAssignment.projectId"
    if (-not $projectIds.Contains($targetProjectId)) {
        throw "Destination project does not exist in current state: $targetProjectId"
    }

    $actualAssignment = Get-AssignmentValue -Assignments $assignments -ThreadId $threadId
    if ($null -eq $actualAssignment -and -not $projectlessIds.Contains($threadId) -and -not $knownThreadIds.Contains($threadId)) {
        throw "Thread is not assigned, projectless, or present in the read-only thread database: $threadId"
    }
    if (-not (Test-AssignmentsEqual -Expected $expectedAssignment -Actual $actualAssignment)) {
        throw "Current assignment changed after plan creation for thread $threadId."
    }
    if (Test-AssignmentsEqual -Expected $targetAssignment -Actual $actualAssignment) {
        throw "Reassignment is a no-op for thread $threadId."
    }

    $validatedOperations += [PSCustomObject]@{
        threadId     = $threadId
        current      = $actualAssignment
        target       = $targetAssignment
    }
}

[PSCustomObject]@{
    valid          = $true
    planId         = [string](Get-NamedPropertyValue -Object $plan -Name 'planId')
    planPath       = $resolvedPlanPath
    statePath      = $resolvedStatePath
    operationCount = $validatedOperations.Count
    knownThreadCount = $knownThreadIds.Count
    operations     = $validatedOperations
}
