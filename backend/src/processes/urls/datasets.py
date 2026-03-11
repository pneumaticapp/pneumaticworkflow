from django.urls import path
from rest_framework.routers import DefaultRouter

from src.processes.views.dataset import DatasetItemViewSet, DatasetViewSet
from src.processes.views.public.dataset import PublicDatasetViewSet

router = DefaultRouter(trailing_slash=False)
router.register('', DatasetViewSet, basename='datasets')

dataset_items_list = DatasetItemViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
dataset_items_detail = DatasetItemViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path(
        '<int:dataset_pk>/items',
        dataset_items_list,
        name='dataset-items-list',
    ),
    path(
        '<int:dataset_pk>/items/<int:pk>',
        dataset_items_detail,
        name='dataset-items-detail',
    ),
    path(
        'public/<int:pk>',
        PublicDatasetViewSet.as_view({'get': 'retrieve'}),
        name='public-dataset-detail',
    ),
]
urlpatterns += router.urls
