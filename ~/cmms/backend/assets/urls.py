from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'assets', AssetViewSet, basename='asset') # The r'assets' part defines the URL prefix for this ViewSet

# The API URLs are now determined automatically by the router.
# These will be included under /api/assets/ in the project's main urls.py
urlpatterns = [
    path('', include(router.urls)),
]
