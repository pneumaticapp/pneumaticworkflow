# ruff: noqa: RUF005
from django.urls import path
from rest_framework.routers import DefaultRouter

from src.reports.views.highlights import HighlightsView
from src.reports.views.tasks import (
    TasksDashboardViewSet,
)
from src.reports.views.workflows import (
    WorkflowsDashboardViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(
    prefix='dashboard/workflows',
    viewset=WorkflowsDashboardViewSet,
    basename='workflows_dashboard',
)
router.register(
    prefix='dashboard/tasks',
    viewset=TasksDashboardViewSet,
    basename='workflows_tasks',
)

urlpatterns = router.urls + [
    path('highlights', HighlightsView.as_view()),
]
