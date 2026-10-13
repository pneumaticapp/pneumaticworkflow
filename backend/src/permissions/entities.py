from typing_extensions import TypedDict


class ObjectPermissionData(TypedDict):

    """Effective permissions of a user on a single object."""

    id: int
    has_view: bool
    has_change: bool
