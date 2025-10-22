from django.urls import include, path

urlpatterns = [
    path(
        'customerio/',
        include('src.analysis.customerio.urls'),
    ),
]
