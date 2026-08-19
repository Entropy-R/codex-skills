[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if (-not $Condition) {
        throw "Assertion failed: $Message"
    }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 20), $utf8NoBom)
}

function Assert-Fails {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$MessagePattern
    )

    $failed = $false
    try {
        & $Action | Out-Null
    }
    catch {
        $failed = $true
        if ($_.Exception.Message -notmatch $MessagePattern) {
            throw "Expected failure matching '$MessagePattern', got: $($_.Exception.Message)"
        }
    }

    if (-not $failed) {
        throw "Expected failure matching '$MessagePattern', but the action succeeded."
    }
}

$scriptsRoot = Split-Path -Parent $PSScriptRoot
$fixturesRoot = Join-Path $PSScriptRoot 'fixtures'
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('codex-conversation-organizer-tests-' + [guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $testRoot)

$validateScript = Join-Path $scriptsRoot 'validate-migration-plan.ps1'
$applyScript = Join-Path $scriptsRoot 'apply-assignment-plan.ps1'
$verifyScript = Join-Path $scriptsRoot 'verify-assignment-plan.ps1'
$collectScript = Join-Path $scriptsRoot 'collect-conversation-inventory.ps1'

foreach ($scriptPath in @($collectScript, $validateScript, $applyScript, $verifyScript)) {
    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $scriptPath,
        [ref]$tokens,
        [ref]$parseErrors
    )
    Assert-True -Condition (@($parseErrors).Count -eq 0) -Message "PowerShell syntax is valid: $scriptPath"
}

$statePath = Join-Path $testRoot 'state.json'
$planPath = Join-Path $testRoot 'valid-plan.json'
$threadDatabasePath = Join-Path $testRoot 'threads.sqlite'
Copy-Item -LiteralPath (Join-Path $fixturesRoot 'state.json') -Destination $statePath
Copy-Item -LiteralPath (Join-Path $fixturesRoot 'valid-plan.json') -Destination $planPath

$sqliteCommand = Get-Command sqlite3.exe -ErrorAction SilentlyContinue
if ($null -eq $sqliteCommand) {
    $sqliteCommand = Get-Command sqlite3 -ErrorAction Stop
}
& $sqliteCommand.Source $threadDatabasePath 'CREATE TABLE threads (id TEXT PRIMARY KEY); INSERT INTO threads(id) VALUES (''thread-a''), (''thread-b''), (''thread-c''), (''thread-d'');'
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create test thread database with exit code $LASTEXITCODE."
}

$validation = & $validateScript -PlanPath $planPath -StatePath $statePath -ThreadDatabasePath $threadDatabasePath
Assert-True -Condition $validation.valid -Message 'Valid fixture plan passes validation.'
Assert-True -Condition ($validation.operationCount -eq 3) -Message 'Assigned, projectless, and legacy unmapped operations are validated.'

$beforeWhatIfHash = (Get-FileHash -LiteralPath $statePath -Algorithm SHA256).Hash
$whatIfResult = & $applyScript -PlanPath $planPath -StatePath $statePath -ThreadDatabasePath $threadDatabasePath -WhatIf
$afterWhatIfHash = (Get-FileHash -LiteralPath $statePath -Algorithm SHA256).Hash
Assert-True -Condition ($whatIfResult.status -eq 'what-if') -Message 'Apply script reports what-if mode.'
Assert-True -Condition ($beforeWhatIfHash -ceq $afterWhatIfHash) -Message 'What-if does not modify state.'

$backupDirectory = Join-Path $testRoot 'backups'
$applyResult = & $applyScript -PlanPath $planPath -StatePath $statePath -ThreadDatabasePath $threadDatabasePath -BackupDirectory $backupDirectory -Confirm:$false
Assert-True -Condition ($applyResult.status -eq 'applied') -Message 'Confirmed fixture plan is applied.'
Assert-True -Condition (Test-Path -LiteralPath $applyResult.backupPath -PathType Leaf) -Message 'Atomic replacement created a backup.'

$writtenState = Get-Content -Raw -LiteralPath $statePath -Encoding UTF8 | ConvertFrom-Json
Assert-True -Condition ($writtenState.'thread-project-assignments'.'thread-a'.projectId -ceq 'project-b') -Message 'Assigned thread moved to Project B.'
Assert-True -Condition ($writtenState.'thread-project-assignments'.'thread-c'.projectId -ceq 'project-b') -Message 'Projectless thread moved to Project B.'
Assert-True -Condition ($writtenState.'thread-project-assignments'.'thread-d'.projectId -ceq 'project-b') -Message 'Legacy unmapped thread moved to Project B after read-only database validation.'
Assert-True -Condition ($writtenState.'thread-project-assignments'.'thread-b'.projectId -ceq 'project-a') -Message 'Unplanned assignment remains unchanged.'
Assert-True -Condition ([bool]$writtenState.'unrelated-state'.mustRemain) -Message 'Unrelated state remains unchanged.'
Assert-True -Condition ('thread-c' -notin @($writtenState.'projectless-thread-ids')) -Message 'Assigned thread is removed from projectless IDs.'

$verifyResult = & $verifyScript -PlanPath $planPath -StatePath $statePath -FailOnMismatch
Assert-True -Condition ($verifyResult.status -eq 'verified') -Message 'Applied plan verifies successfully.'

Assert-Fails -Action {
    & $applyScript -PlanPath $planPath -StatePath $statePath -ThreadDatabasePath $threadDatabasePath -BackupDirectory $backupDirectory -Confirm:$false
} -MessagePattern 'changed after plan creation'

$unapprovedStatePath = Join-Path $testRoot 'unapproved-state.json'
$unapprovedPlanPath = Join-Path $testRoot 'unapproved-plan.json'
Copy-Item -LiteralPath (Join-Path $fixturesRoot 'state.json') -Destination $unapprovedStatePath
$unapprovedPlan = Get-Content -Raw -LiteralPath (Join-Path $fixturesRoot 'valid-plan.json') -Encoding UTF8 | ConvertFrom-Json
$unapprovedPlan.approval.confirmed = $false
Write-JsonFile -Value $unapprovedPlan -Path $unapprovedPlanPath
Assert-Fails -Action {
    & $validateScript -PlanPath $unapprovedPlanPath -StatePath $unapprovedStatePath
} -MessagePattern 'not explicitly confirmed'

$duplicateStatePath = Join-Path $testRoot 'duplicate-state.json'
$duplicatePlanPath = Join-Path $testRoot 'duplicate-plan.json'
Copy-Item -LiteralPath (Join-Path $fixturesRoot 'state.json') -Destination $duplicateStatePath
$duplicatePlan = Get-Content -Raw -LiteralPath (Join-Path $fixturesRoot 'valid-plan.json') -Encoding UTF8 | ConvertFrom-Json
$duplicatePlan.operations = @($duplicatePlan.operations[0], $duplicatePlan.operations[0])
Write-JsonFile -Value $duplicatePlan -Path $duplicatePlanPath
Assert-Fails -Action {
    & $validateScript -PlanPath $duplicatePlanPath -StatePath $duplicateStatePath
} -MessagePattern 'Duplicate threadId'

$unknownStatePath = Join-Path $testRoot 'unknown-state.json'
$unknownPlanPath = Join-Path $testRoot 'unknown-plan.json'
Copy-Item -LiteralPath (Join-Path $fixturesRoot 'state.json') -Destination $unknownStatePath
$unknownPlan = Get-Content -Raw -LiteralPath (Join-Path $fixturesRoot 'valid-plan.json') -Encoding UTF8 | ConvertFrom-Json
$unknownPlan.operations = @($unknownPlan.operations[0])
$unknownPlan.operations[0].targetAssignment.projectId = 'missing-project'
Write-JsonFile -Value $unknownPlan -Path $unknownPlanPath
Assert-Fails -Action {
    & $validateScript -PlanPath $unknownPlanPath -StatePath $unknownStatePath
} -MessagePattern 'Destination project does not exist'

[PSCustomObject]@{
    status   = 'passed'
    testRoot = $testRoot
    checks   = 15
}
