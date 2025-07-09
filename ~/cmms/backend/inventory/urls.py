from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SparePartCategoryViewSet,
    VendorViewSet,
    WarehouseViewSet,
    SparePartViewSet,
    StockItemViewSet,
    PartReservationViewSet
)

router = DefaultRouter()
router.register(r'categories', SparePartCategoryViewSet, basename='sparepartcategory')
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'parts', SparePartViewSet, basename='sparepart')
router.register(r'stock-items', StockItemViewSet, basename='stockitem')
router.register(r'reservations', PartReservationViewSet, basename='partreservation')

urlpatterns = [
    path('', include(router.urls)),
]
