from user_agents import parse


def get_user_agent(request) -> str:
    user_agent = parse(request.META.get('HTTP_USER_AGENT') or '')
    return (
        f'{user_agent.device.family}/'
        f'{user_agent.os.family}/'
        f'{user_agent.browser.family}'
    )
