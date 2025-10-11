from django.urls import include, path


urlpatterns = [
    path(
        'customerio/',
        include('src.analytics.customerio.urls'),
    ),
]
