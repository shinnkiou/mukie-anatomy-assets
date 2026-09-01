# NEVER TEAR Building Queue — Fresh Automation Bootstrap

Status: `TO_BE_CREATED_IN_NEW_CHATGPT_PROJECT`.

Do not reuse BP3D schedules. Create a fresh Automation only after the user supplies cadence/time.

Recommended title: `NEVER TEAR Building Queue`

Recommended execution prompt:

> Read the NEVER TEAR Building Factory project canon and current task queue. Select the highest-priority runnable unfinished task whose dependencies are satisfied. Continue from its saved next_action. Execute research/design/implementation/QA as needed within the current run budget, preserving immutable source/master data. Separate Structure Pass from Surface Pass. Prefer textures/normal/AO for microdetail that does not require silhouette geometry. If blocked, record the blocker and continue with the next runnable task. Before ending the run, save artifacts to the designated canonical stores, read them back, update the task status/next_action, and report completed work, failures and the next starting point. Do not mark a task COMPLETE until relevant QA and canonical readback pass.

Timing rules:
- explicit clock time → exact schedule
- user-provided daypart → flexible schedule
- cadence without timing detail → resolve timing when the Automation is actually created; do not invent a permanent bootstrap time
- default work target per run: recoverable checkpoint within 25 minutes

Pause/stop when the user requests it, when all tasks are COMPLETE with no new tasks, or when a project-wide blocker prevents every runnable task. When the queue is empty, report that fact rather than inventing new construction goals.
