from .models import WebHook


def find_and_fire_hook(event_name: str, instance, **kwargs):
    user = kwargs['user_override']
    hooks = WebHook.objects.on_account(user.account_id).for_event(event_name)

    for hook in hooks:
        hook.deliver_hook(instance)
