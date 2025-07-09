from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FaultCategoryViewSet,
    RootCauseViewSet,
    BreakdownReportViewSet
)

router = DefaultRouter()
router.register(r'fault-categories', FaultCategoryViewSet, basename='faultcategory')
router.register(r'root-causes', RootCauseViewSet, basename='rootcause')
router.register(r'breakdown-reports', BreakdownReportViewSet, basename='breakdownreport')

urlpatterns = [
    path('', include(router.urls)),
]
