# Offline local-state safety

Read this reference only for reassignment of existing local Codex conversations. The procedure is intentionally conservative because the state format is internal and may change between app versions.

## Preconditions

- A reviewable classification exists and the user confirmed each reassignment operation.
- Every source thread ID and destination project ID was resolved from current state rather than invented.
- The plan records the expected current assignment for compare-and-swap validation.
- The active organizing thread is not in the operation list.
- The plan contains reassignment only; continuation tasks are created through app tools.

## Prepare inside Codex

1. Generate the approved plan in a user-visible working or temporary directory.
2. Run `validate-migration-plan.ps1` against the current state.
3. Run `apply-assignment-plan.ps1 -WhatIf` and review its operation summary.
4. Give the user the exact PowerShell command to run outside Codex and the expected backup location.
5. Do not launch a hidden helper that waits for Codex to exit.

## Apply outside Codex

The user closes Codex and runs the approved command in PowerShell. The apply script must:

- Refuse to operate on the default Codex state while a `ChatGPT` desktop process is running.
- Parse and validate both plan and state before writing.
- Confirm that every current assignment still matches the plan's expected assignment.
- For a legacy thread with no assignment or projectless record, confirm its ID exists in `state_5.sqlite` through a read-only query before adding an assignment.
- Confirm that every destination project still exists.
- Create a timestamped backup through the atomic replacement operation.
- Modify only `thread-project-assignments` and remove newly assigned threads from `projectless-thread-ids` when present.
- Preserve unknown and unrelated fields.
- Never touch `state_5.sqlite`, session rollouts, messages, thread working directories, or repository files.
- Stop on an unfamiliar or missing required state structure instead of guessing.

## Verify after restart

Run `verify-assignment-plan.ps1`, inspect projects in the app, and confirm that original tasks remain readable. Report deviations and the backup path. Do not automatically restore a backup; restoration is a separate destructive overwrite requiring explicit authorization.

## Plan contract

An offline plan uses schema version 1 and contains:

- `planId` and `createdAt`.
- `classificationPolicy.originalUserText` and the interpretation used for the run.
- `approval.confirmed`, `approval.confirmedAt`, and per-operation `approved` flags.
- Reassignment operations with `threadId`, `currentAssignment`, `targetAssignment`, and a classification reason.

`currentAssignment` is `null` for a projectless thread or an object with `projectKind` and `projectId`. The apply script performs no classification and rejects unapproved, duplicate, stale, no-op, or unknown-destination operations.

Minimal example:

```json
{
  "schemaVersion": 1,
  "planId": "generated-unique-id",
  "createdAt": "2026-08-19T00:00:00Z",
  "classificationPolicy": {
    "originalUserText": "The user's exact natural-language policy.",
    "interpretedSummary": [
      "Only the individually listed conversations will be reassigned."
    ]
  },
  "approval": {
    "confirmed": true,
    "confirmedAt": "2026-08-19T00:10:00Z"
  },
  "operations": [
    {
      "threadId": "resolved-thread-id",
      "action": "reassign",
      "currentAssignment": {
        "projectKind": "local",
        "projectId": "resolved-source-project-id"
      },
      "targetAssignment": {
        "projectKind": "local",
        "projectId": "resolved-destination-project-id"
      },
      "classification": {
        "status": "clear",
        "reason": "Concise explanation tied to the user's policy and observed evidence."
      },
      "approved": true
    }
  ]
}
```

Keep `approval.confirmed` and every operation's `approved` value false until the user confirms the displayed operation list. Do not pre-authorize a plan merely to run validation.
