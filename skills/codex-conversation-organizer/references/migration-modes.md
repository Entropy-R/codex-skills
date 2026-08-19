# Migration modes

Choose a mode after classification and before asking for execution approval.

## Plan only

Use when the user asks to inspect, classify, preview, or propose organization. Produce no writes, new tasks, archives, or project changes.

## Reassign an existing conversation

Use for historical organization when the user wants the original thread ID and full history to appear under another saved Codex project.

Reassignment changes only the desktop app's project-assignment metadata. It does not change:

- The thread ID or message history.
- The thread's original working directory.
- Repository state, terminal processes, attachments, or generated files.
- SQLite thread rows or rollout files.

Because arbitrary cross-project reassignment is not exposed as a public app tool, this mode is version-sensitive and must use the offline safety procedure. Describe it as local metadata reassignment rather than a supported repository handoff.

## Create a continuation task

Use when future work must run in the destination project's directory or environment.

Continuation mode here is part of organizing one or more existing conversations across projects. If the sole request is to summarize or hand off the current task to a new conversation, use a dedicated handoff workflow instead of triggering bulk conversation organization.

Create the task with the app's project task-creation capability. Include only the context needed to continue:

- Source task title and thread ID.
- Original request and current objective.
- Confirmed decisions and constraints.
- Relevant artifacts, repositories, files, commits, or outputs when applicable.
- Completed work, remaining work, risks, and verification state.

Do not claim that terminal processes, uncommitted changes, attachments, or full history were copied unless separately verified. The new task has a new thread ID. Preserve the source task by default.

## Source disposition after continuation

Offer source disposition only after every destination continuation has been created and verified. This choice applies to continuation mode because reassignment moves the original thread and does not create an old duplicate.

- `keep` — Default. Leave the source unchanged and report that it was retained.
- `archive` — Use the supported archive capability after the user confirms the exact source tasks. This is reversible and is the preferred alternative when the user wants the old tasks out of the active list.
- `delete` — Permanent deletion. Require a separate post-verification confirmation that lists the exact source task titles and IDs and states that deletion may be irreversible.

Before offering or executing `delete`, check whether the current Codex environment exposes a verified supported delete capability. Do not equate archive with deletion. If no supported delete capability exists, report that permanent deletion is unavailable in the current environment, keep the sources, and offer archive instead. Never delete database rows, rollout files, session indexes, attachments, or directories to emulate an unavailable product action.

An initial request such as "move these and delete the originals" records the user's preference but does not authorize pre-verification deletion. Ask for the exact destructive confirmation after the destination tasks verify. If the user does not answer the disposition question, use `keep` without further mutation.

## Mixed plans

A run may reassign completed historical conversations and create continuation tasks for active work. Show the mode per conversation and obtain approval for the concrete operation list. Offline reassignment and in-app continuation are separate execution phases and must be verified separately. Record source disposition per verified continuation; omitted values normalize to `keep`.

## Approval boundary

Approval of the natural-language policy authorizes classification only. Approval to execute must identify each thread, destination project, and migration mode. Migration approval does not authorize source archive or deletion. Source disposition requires its own post-verification decision, with deletion requiring the strongest exact confirmation. Do not infer permission to change working directories or move repository data.
