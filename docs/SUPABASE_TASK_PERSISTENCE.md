# Supabase persistence

ENGINEER OS uses Supabase as the durable metadata/state layer. Large engineering
files are referenced by URI and are not copied into the task database.

## Existing database model

The connected `engineer-os` Supabase project already contains the engineering
task/orchestration schema. The Task Engine adapter maps ENGINEER OS tasks to
`public.engineering_tasks` and preserves execution state in the existing
engineering task model.

The adapter deliberately does not create a second task queue or a second
orchestration framework.

## Runtime configuration

Set these environment variables on the worker/runtime that executes ENGINEER OS:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ENGINEER_OS_OWNER_ID`

Never commit the service-role key to GitHub.

Example:

```text
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<secret>
ENGINEER_OS_OWNER_ID=<auth-user-uuid>
```

## Python

```python
from engineering.core import TaskEngine, SupabaseTaskStore

store = SupabaseTaskStore()
engine = TaskEngine(store=store)
```

`TaskEngine` remains independent of Supabase. Tests can continue using the local `TaskStore`.

## Mapping

| ENGINEER OS | Supabase |
| --- | --- |
| task_id | `engineering_tasks.provenance.engineer_os_task_id` |
| ТЗ | `engineering_tasks.objective` |
| materials | `engineering_tasks.input_refs` |
| requested checks | `engineering_tasks.prerequisites` |
| lifecycle status | `engineering_tasks.status` |
| result status/error | `engineering_tasks.provenance` |
| project UUID | `engineering_tasks.project_id` |

If `project_id` is not a valid UUID, it is kept in provenance rather than inventing a database relationship.

## Security

The adapter expects a server-side service-role credential. It must only run in
a trusted backend/worker environment, never in the browser.