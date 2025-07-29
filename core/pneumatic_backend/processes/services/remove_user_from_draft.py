from pneumatic_backend.processes.models import TemplateDraft


def remove_user_from_draft(account_id: int, user_id: int):
    for draft in TemplateDraft.objects.by_user(account_id, user_id):
        draft.remove_user(user_id)
