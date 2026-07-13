# План тестирования UserService._check_and_complete_tasks

## Имитируемые вызовы (mock)

Имитировать:
- check_and_complete_tasks.delay()
  - Путь патча: `src.accounts.services.user.check_and_complete_tasks.delay`

Не имитировать:
- Task.objects
- TaskQuerySet.active()
- TaskQuerySet.active_for_user()
- QuerySet.values_list()
- self.instance.id, self.is_superuser, self.auth_type, self.account.id

## Граф зависимостей (1 уровень)

```
UserService._check_and_complete_tasks
├── TaskQuerySet.active()
├── TaskQuerySet.active_for_user()
├── QuerySet.values_list()
└── check_and_complete_tasks.delay()
```

## Test cases

| Annotation | Function name | Description | Expected result |
|------------|---------------|-------------|-----------------|
| No matching tasks | test_check_and_complete_tasks_no_matching_tasks_skip | `UserService` is created with default constructor parameters (`is_superuser=False`, `auth_type=USER`). `self.instance` has no tasks returned by `Task.objects.active().active_for_user(self.instance.id)`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Default parameters with matching task | test_check_and_complete_tasks_default_params_matching_task_ok | `UserService` is created with default constructor parameters. `self.instance` is a direct performer on one `ACTIVE` task in a `RUNNING` workflow with `require_completion_by_all=False`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called once with `task_ids` containing only that task id, `is_superuser=False`, `auth_type=USER`, and `account_id=self.account.id`. |
| Single matching task | test_check_and_complete_tasks_single_matching_task_ok | `self.instance` is a direct performer on exactly one task that matches `active().active_for_user()`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called once; `task_ids` contains the id of that task. |
| Multiple matching tasks | test_check_and_complete_tasks_multiple_matching_tasks_ok | `self.instance` is a performer on several tasks that all match `active().active_for_user()`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called once; `task_ids` contains the ids of all matching tasks. |
| Mixed matching and non-matching tasks | test_check_and_complete_tasks_mixed_matching_tasks_ok | `self.instance` is linked to multiple tasks; some match `active().active_for_user()` and some do not (wrong status, workflow, or performer rules). `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called once; `task_ids` contains only ids of matching tasks. |
| Filters by instance id | test_check_and_complete_tasks_filters_by_instance_id_ok | `UserService` is constructed with `user` and `instance` pointing to different users on the same account. Only `self.instance` is a performer on a matching task; `self.user` is a performer on a different matching task. `_check_and_complete_tasks()` is called. | `task_ids` contains only the task id where `self.instance` is the performer. |
| `is_superuser=True` | test_check_and_complete_tasks_is_superuser_true_ok | `UserService(..., is_superuser=True)` is used. `self.instance` has one matching task. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called with `is_superuser=True`. |
| Custom `auth_type` | test_check_and_complete_tasks_custom_auth_type_ok | `UserService(..., auth_type=AuthTokenType.GUEST)` (or another non-default value). `self.instance` has one matching task. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called with the same `auth_type` passed to the constructor. |
| `account_id` from service account | test_check_and_complete_tasks_account_id_from_service_ok | `UserService` is created for a user on account A. `self.instance` belongs to account A and has one matching task. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is called with `account_id` equal to `self.account.id`. |
| Direct performer, completion not required | test_check_and_complete_tasks_direct_performer_no_compl_req_ok | Task is `ACTIVE`, workflow is `RUNNING`, `require_completion_by_all=False`, `self.instance` is a direct user performer. `_check_and_complete_tasks()` is called. | The task id is included in `task_ids`. |
| Direct performer, completion required, not completed | test_check_and_complete_tasks_direct_performer_compl_req_ok | Task is `ACTIVE`, workflow is `RUNNING`, `require_completion_by_all=True`, `self.instance` is a direct performer with `is_completed=False`. `_check_and_complete_tasks()` is called. | The task id is included in `task_ids`. |
| Group performer, user in group | test_check_and_complete_tasks_group_performer_in_group_ok | Task is `ACTIVE`, workflow is `RUNNING`, performer is a group that includes `self.instance`. `_check_and_complete_tasks()` is called. | The task id is included in `task_ids`. |
| Two workflows on same account | test_check_and_complete_tasks_two_workflows_same_account_ok | `self.instance` is a performer on matching tasks in two different `RUNNING` workflows of the same account. `_check_and_complete_tasks()` is called. | `task_ids` contains both task ids. |
| Excludes completed task | test_check_and_complete_tasks_excludes_completed_task_skip | Task status is `COMPLETED`; `self.instance` is a performer. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes pending task | test_check_and_complete_tasks_excludes_pending_task_skip | Task status is `PENDING`; `self.instance` is a performer. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes delayed task | test_check_and_complete_tasks_excludes_delayed_task_skip | Task status is `DELAYED`; `self.instance` is a performer. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes non-running workflow | test_check_and_complete_tasks_excludes_non_running_wf_skip | Task is `ACTIVE` but workflow status is not `RUNNING`; `self.instance` is a performer. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes non-performer | test_check_and_complete_tasks_excludes_non_performer_skip | Task is `ACTIVE` in a `RUNNING` workflow; `self.instance` is not a direct or group performer. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes completed performer when all must complete | test_check_and_complete_tasks_excludes_compl_performer_all_req_skip | Task is `ACTIVE`, workflow is `RUNNING`, `require_completion_by_all=True`, `self.instance` is a direct performer with `is_completed=True`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes deleted direct performer | test_check_and_complete_tasks_excludes_deleted_performer_skip | Task is `ACTIVE`, workflow is `RUNNING`, `self.instance` is a direct performer with `directly_status=DELETED`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes group performer when user not in group | test_check_and_complete_tasks_excl_grp_perf_not_in_group_skip | Task is `ACTIVE`, workflow is `RUNNING`, performer is a group that does not include `self.instance`. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |
| Excludes task from another account | test_check_and_complete_tasks_excludes_other_account_task_skip | `self.instance` is a performer on an `ACTIVE` task in a `RUNNING` workflow belonging to a different account. `_check_and_complete_tasks()` is called. | `check_and_complete_tasks.delay` is not called. |

## Implementation notes

- Patch `src.accounts.services.user.check_and_complete_tasks.delay`, not `_check_and_complete_tasks` itself.
- Fixtures: `create_test_account`, `create_test_owner`, `create_test_admin` (accounts); `create_test_workflow` (`processes.tests.fixtures`).
- Test module: `test_user_check_and_complete_tasks.py` next to `test_user.py`.