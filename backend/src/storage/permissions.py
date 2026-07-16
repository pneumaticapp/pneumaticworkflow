from src.generics.permissions import BaseAuthPermission


class IsAuthenticatedOrPublicTemplate(BaseAuthPermission):
    """
    Allows access if the user is authenticated (any type)
    OR if a valid public template token is present.
    Used by check_permission endpoint to support
    both authenticated users and public form submissions.
    """

    def has_permission(self, request, view):
        if self._is_authenticated(request):
            return True
        return bool(getattr(request, 'public_template', None))
