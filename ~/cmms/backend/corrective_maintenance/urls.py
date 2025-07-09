from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FaultCategoryViewSet,
    RootCauseViewSet,
    BreakdownReportViewSet
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'fault-categories', FaultCategoryViewSet, basename='faultcategory')
router.register(r'root-causes', RootCauseViewSet, basename='rootcause')
router.register(r'breakdown-reports', BreakdownReportViewSet, basename='breakdownreport')

# The API URLs are now determined automatically by the router.
# These will be included under the /api/cm/ prefix in the project's main urls.py
urlpatterns = [
    path('', include(router.urls)),
]
