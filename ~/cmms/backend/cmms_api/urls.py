"""cmms_api URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App APIs
    path('api/assets/', include('assets.urls')),
    path('api/pm/', include('preventive_maintenance.urls')),
    path('api/cm/', include('corrective_maintenance.urls')),
    path('api/wo/', include('work_orders.urls')),
    path('api/inventory/', include('inventory.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
