from django.urls import path

from src.authentication.views.consent import ConsentView, LoginCodeView
from src.authentication.views.delegation import (
    DelegationView,
    IntrospectionView,
)
from src.authentication.views.oauth import (
    ResourceMetadataView,
    ServerMetadataView,
)
from src.authentication.views.connections import (
    ConnectionRevokeView,
    ConnectionsView,
)
from src.mcp.views.files import (
    AttachmentDetailView,
    FileValidationView,
    UploadCleanupView,
    UploadCompletionView,
)
from src.mcp.views.templates import KickoffView
from src.mcp.views.uploads import (
    UploadAttachView,
    UploadCreateView,
    UploadImportView,
    UploadStatusView,
    UploadTokenView,
)

urlpatterns = [
    path('internal/mcp/introspect', IntrospectionView.as_view()),
    path('internal/mcp/delegate', DelegationView.as_view()),
    path('internal/mcp/validate-files', FileValidationView.as_view()),
    path(
        'internal/mcp/complete-upload',
        UploadCompletionView.as_view(),
    ),
    path('internal/mcp/cleanup-upload', UploadCleanupView.as_view()),
    path('integrations/mcp/login-code', LoginCodeView.as_view()),
    path('integrations/mcp/consent', ConsentView.as_view()),
    path('integrations/mcp/connections', ConnectionsView.as_view()),
    path(
        'integrations/mcp/connections/<uuid:connection_id>',
        ConnectionRevokeView.as_view(),
    ),
    path('integrations/mcp/uploads', UploadCreateView.as_view()),
    path(
        'integrations/mcp/uploads/<uuid:session_id>',
        UploadStatusView.as_view(),
    ),
    path(
        'integrations/mcp/uploads/<uuid:session_id>/token',
        UploadTokenView.as_view(),
    ),
    path(
        'integrations/mcp/uploads/<uuid:session_id>/import',
        UploadImportView.as_view(),
    ),
    path(
        'integrations/mcp/uploads/<uuid:session_id>/attach',
        UploadAttachView.as_view(),
    ),
    path(
        'integrations/mcp/templates/<int:template_id>/kickoff',
        KickoffView.as_view(),
    ),
    path(
        'integrations/mcp/attachments/<int:attachment_id>',
        AttachmentDetailView.as_view(),
    ),
    path(
        '.well-known/oauth-authorization-server',
        ServerMetadataView.as_view(),
    ),
    path(
        '.well-known/oauth-protected-resource',
        ResourceMetadataView.as_view(),
    ),
    path(
        '.well-known/oauth-protected-resource/mcp',
        ResourceMetadataView.as_view(),
    ),
]
