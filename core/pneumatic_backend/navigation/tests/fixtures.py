from pneumatic_backend.navigation.models import (
    Menu,
    MenuItem
)
from pneumatic_backend.navigation.enums import MenuType


def create_test_menu(
    slug=MenuType.HELP_CENTER,
    link=None,
    label='Help Center',
    count_items=2
):
    menu = Menu.objects.create(
        slug=slug,
        label=label,
        link=link
    )
    for order in range(1, count_items + 1):
        MenuItem.objects.create(
            menu=menu,
            link='http://my.link',
            label=f'Link {order}',
            order=order
        )
    return menu
