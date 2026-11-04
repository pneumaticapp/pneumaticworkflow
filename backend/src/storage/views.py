from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
)
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import IsAuthenticated
from src.openapi.permission_docs import ACCESS_ATTACHMENT
from src.openapi.responses import EMPTY, UNAUTHORIZED, VALIDATION_ERROR
from src.openapi.helpers import with_access_text
from src.storage.models import Attachment
from src.storage.paginations import AttachmentListPagination
from src.storage.permissions import (
    IsAuthenticatedOrPublicTemplate,
)
from src.storage.serializers import (
    AttachmentCheckPermissionSerializer,
    AttachmentListFilterSerializer,
    AttachmentListSerializer,
    AttachmentSerializer,
)
from src.storage.services.attachments import AttachmentService


class AttachmentViewSet(
    ListModelMixin,
    CustomViewSetMixin,
    GenericViewSet,
):
    """
    ViewSet for working with attachments.
    Provides endpoint for checking file access permissions.
    """

    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.all()

    action_serializer_classes = {
        'check_permission': AttachmentCheckPermissionSerializer,
        'list': AttachmentListSerializer,
    }
    action_paginator_classes = {
        'list': AttachmentListPagination,
    }

    def get_permissions(self):
        if self.action == 'check_permission':
            return (IsAuthenticatedOrPublicTemplate(),)
        return (IsAuthenticated(),)

    @extend_schema(
        tags=['Attachments'],
        summary='Check file access for the file service',
        description=(
            'Internal authorization callback used by Files API. Accepts '
            'an authenticated user/guest or a public template token. '
            'Checks the attachment ownership and its workflow/template '
            'access; an unknown or inaccessible file returns empty 403.'
        ),
        request=AttachmentCheckPermissionSerializer,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: EMPTY,
        },
    )
    @action(
        methods=['POST'],
        detail=False,
        url_path='check-permission',
    )
    def check_permission(self, request, *args, **kwargs):
        """
        Checks user permission to access file.
        Used by file service for authorization.

        Returns:
        - 204: Access granted
        - 400: Validation error
        - 401: Not authenticated
        - 403: Access denied or file not found
        """
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        public_template = getattr(request, 'public_template', None)
        if request.user.is_authenticated:
            user = request.user
            user_id = user.id
            account_id = user.account_id
        else:
            user = None
            user_id = None
            account_id = (
                public_template.account_id
                if public_template else None
            )

        service = AttachmentService(user=user)
        has_permission = service.check_user_permission(
            user_id=user_id,
            account_id=account_id,
            file_id=slz.validated_data['file_id'],
            public_template=public_template,
        )

        if has_permission:
            return self.response_ok()
        return self.response_forbidden()

    @extend_schema(
        tags=['Attachments'],
        summary='List attachments',
        description=with_access_text(
            (
                'Attachments accessible to the current user. '
                'Default sort by id. Paginated via limit/offset.'
            ),
            ACCESS_ATTACHMENT,
        ),
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            # Item serializer; spectacular wraps with pagination.
            200: AttachmentListSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
        },
    )
    def list(self, request, *args, **kwargs):
        """Returns list of attachments accessible to user."""
        filter_slz = AttachmentListFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        qst = Attachment.objects.raw_list_query(
            user=request.user,
            **filter_slz.validated_data,
        )
        return self.paginated_response(qst)
