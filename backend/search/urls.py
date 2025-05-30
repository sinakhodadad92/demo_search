from django.urls import path
from .views import SearchView, DocDetailView, HealthCheckView

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('doc/<str:id>/', DocDetailView.as_view(), name='doc-detail'),
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
]