from django.urls import path
from rest_framework.routers import DefaultRouter

from pneumatic_backend.reports.views.highlights import HighlightsView
from pneumatic_backend.reports.views.workflows import (
    WorkflowsDashboardViewSet
)
from pneumatic_backend.reports.views.tasks import (
    TasksDashboardViewSet
)
router = DefaultRouter(trailing_slash=False)
router.register(
    prefix='dashboard/workflows',
    viewset=WorkflowsDashboardViewSet,
    basename='workflows_dashboard'
)
router.register(
    prefix='dashboard/tasks',
    viewset=TasksDashboardViewSet,
    basename='workflows_tasks'
)

urlpatterns = router.urls + [
    path('highlights', HighlightsView.as_view()),
]
