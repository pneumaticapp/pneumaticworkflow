from django.urls import include, path


urlpatterns = [
    path(
        'customerio/',
        include('pneumatic_backend.analytics.customerio.urls')
    )
]
