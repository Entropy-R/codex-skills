[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath,

    [string]$StatePath,

    [string]$CodexHome,

    [string]$BackupDirectory,

    [string]$ResultPath,

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

    return [string](Get-NamedPropertyValue -Object $Expected -Name 'projectKind') -ceq
        [string](Get-NamedPropertyValue -Object $Actual -Name 'projectKind') -and
        [string](Get-NamedPropertyValue -Object $Expected -Name 'projectId') -ceq
        [string](Get-NamedPropertyValue -Object $Actual -Name 'projectId')
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    $json = $Value | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($Path, $json, $utf8NoBom)
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
$defaultStatePath = [System.IO.Path]::GetFullPath((Join-Path $resolvedCodexHome '.codex-global-state.json'))
if ([string]::IsNullOrWhiteSpace($StatePath)) {
    $StatePath = $defaultStatePath
}

$resolvedPlanPath = [System.IO.Path]::GetFullPath($PlanPath)
$resolvedStatePath = [System.IO.Path]::GetFullPath($StatePath)

$validatorPath = Join-Path $PSScriptRoot 'validate-migration-plan.ps1'
$validationParameters = @{
    PlanPath = $resolvedPlanPath
    StatePath = $resolvedStatePath
    CodexHome = $resolvedCodexHome
}
if (-not [string]::IsNullOrWhiteSpace($ThreadDatabasePath)) {
    $validationParameters.ThreadDatabasePath = $ThreadDatabasePath
}
$validation = & $validatorPath @validationParameters

$isDefaultCodexState = [string]::Equals(
    $resolvedStatePath,
    $defaultStatePath,
    [System.StringComparison]::OrdinalIgnoreCase
)

if (-not $WhatIfPreference -and $isDefaultCodexState) {
    $runningDesktopProcesses = @(Get-Process -Name 'ChatGPT' -ErrorAction SilentlyContinue)
    if ($runningDesktopProcesses.Count -gt 0) {
        throw 'Codex Desktop is still running. Close every Codex/ChatGPT desktop window, wait for ChatGPT.exe to exit, and run this command again.'
    }
}

$plan = Get-Content -Raw -LiteralPath $resolvedPlanPath -Encoding UTF8 | ConvertFrom-Json
$state = Get-Content -Raw -LiteralPath $resolvedStatePath -Encoding UTF8 | ConvertFrom-Json
$assignments = Get-NamedPropertyValue -Object $state -Name 'thread-project-assignments'
$projectlessProperty = $state.PSObject.Properties['projectless-thread-ids']

foreach ($operation in @($plan.operations)) {
    $threadId = [string]$operation.threadId
    $actualAssignment = Get-AssignmentValue -Assignments $assignments -ThreadId $threadId
    if (-not (Test-AssignmentsEqual -Expected $operation.currentAssignment -Actual $actualAssignment)) {
        throw "Current assignment changed during apply preparation for thread $threadId."
    }
}

$operationSummary = @($plan.operations | ForEach-Object {
    [PSCustomObject]@{
        threadId       = [string]$_.threadId
        fromProjectId  = if ($null -eq $_.currentAssignment) { $null } else { [string]$_.currentAssignment.projectId }
        toProjectId    = [string]$_.targetAssignment.projectId
    }
})

$actionDescription = "Apply $($operationSummary.Count) confirmed Codex conversation project reassignment(s)"
if (-not $PSCmdlet.ShouldProcess($resolvedStatePath, $actionDescription)) {
    return [PSCustomObject]@{
        status          = 'what-if'
        planId          = [string]$plan.planId
        statePath       = $resolvedStatePath
        operationCount  = $operationSummary.Count
        operations      = $operationSummary
        validation      = $validation
    }
}

if ([string]::IsNullOrWhiteSpace($BackupDirectory)) {
    if ($isDefaultCodexState) {
        $BackupDirectory = Join-Path $resolvedCodexHome 'conversation-organizer-backups'
    }
    else {
        $BackupDirectory = Join-Path (Split-Path -Parent $resolvedStatePath) 'conversation-organizer-backups'
    }
}

$resolvedBackupDirectory = [System.IO.Path]::GetFullPath($BackupDirectory)
[void](New-Item -ItemType Directory -Path $resolvedBackupDirectory -Force)

$beforeHash = (Get-FileHash -LiteralPath $resolvedStatePath -Algorithm SHA256).Hash

foreach ($operation in @($plan.operations)) {
    $threadId = [string]$operation.threadId
    $newAssignment = [PSCustomObject]@{
        projectKind = [string]$operation.targetAssignment.projectKind
        projectId   = [string]$operation.targetAssignment.projectId
    }

    $assignmentProperty = $assignments.PSObject.Properties[$threadId]
    if ($null -eq $assignmentProperty) {
        $assignments | Add-Member -NotePropertyName $threadId -NotePropertyValue $newAssignment
    }
    else {
        $assignmentProperty.Value = $newAssignment
    }

    if ($null -ne $projectlessProperty) {
        $projectlessProperty.Value = @($projectlessProperty.Value | Where-Object {
            [string]$_ -cne $threadId
        })
    }
}

$stateDirectory = Split-Path -Parent $resolvedStatePath
$stateFileName = Split-Path -Leaf $resolvedStatePath
$temporaryPath = Join-Path $stateDirectory ('.' + $stateFileName + '.organizer.' + [guid]::NewGuid().ToString('N') + '.tmp')
$backupName = (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + $stateFileName
$backupPath = Join-Path $resolvedBackupDirectory $backupName

Write-JsonFile -Value $state -Path $temporaryPath
$null = Get-Content -Raw -LiteralPath $temporaryPath -Encoding UTF8 | ConvertFrom-Json

$currentHash = (Get-FileHash -LiteralPath $resolvedStatePath -Algorithm SHA256).Hash
if ($currentHash -cne $beforeHash) {
    throw 'Codex state changed after validation. No replacement was performed.'
}

[System.IO.File]::Replace($temporaryPath, $resolvedStatePath, $backupPath, $true)

$writtenState = Get-Content -Raw -LiteralPath $resolvedStatePath -Encoding UTF8 | ConvertFrom-Json
$writtenAssignments = Get-NamedPropertyValue -Object $writtenState -Name 'thread-project-assignments'
foreach ($operation in @($plan.operations)) {
    $actualAssignment = Get-AssignmentValue -Assignments $writtenAssignments -ThreadId ([string]$operation.threadId)
    if (-not (Test-AssignmentsEqual -Expected $operation.targetAssignment -Actual $actualAssignment)) {
        throw "Post-write verification failed for thread $($operation.threadId). Backup: $backupPath"
    }
}

$result = [PSCustomObject]@{
    status          = 'applied'
    planId          = [string]$plan.planId
    statePath       = $resolvedStatePath
    backupPath      = $backupPath
    beforeSha256    = $beforeHash
    afterSha256     = (Get-FileHash -LiteralPath $resolvedStatePath -Algorithm SHA256).Hash
    operationCount  = $operationSummary.Count
    operations      = $operationSummary
}

if (-not [string]::IsNullOrWhiteSpace($ResultPath)) {
    $resolvedResultPath = [System.IO.Path]::GetFullPath($ResultPath)
    $resultDirectory = Split-Path -Parent $resolvedResultPath
    if (-not [string]::IsNullOrWhiteSpace($resultDirectory)) {
        [void](New-Item -ItemType Directory -Path $resultDirectory -Force)
    }
    Write-JsonFile -Value $result -Path $resolvedResultPath
}

return $result
