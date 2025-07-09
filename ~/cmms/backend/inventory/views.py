from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction, IntegrityError
from django.utils import timezone

from .models import (
    SparePartCategory,
    Vendor,
    Warehouse,
    SparePart,
    StockItem,
    PartReservation
)
from .serializers import (
    SparePartCategorySerializer,
    VendorSerializer,
    WarehouseSerializer,
    SparePartSerializer,
    StockItemSerializer,
    PartReservationSerializer
)

class SparePartCategoryViewSet(viewsets.ModelViewSet):
    queryset = SparePartCategory.objects.all().prefetch_related('child_categories').order_by('name')
    serializer_class = SparePartCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'description']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['parent_category']

class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all().order_by('name')
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'contact_person', 'email']

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('name')
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'location_description']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

class SparePartViewSet(viewsets.ModelViewSet):
    queryset = SparePart.objects.all().select_related('category', 'default_vendor').order_by('name')
    serializer_class = SparePartSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'default_vendor', 'unit_of_measure']
    search_fields = ['name', 'part_number', 'description']

class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.all().select_related('spare_part', 'warehouse', 'spare_part__category').order_by('spare_part__name')
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'spare_part': ['exact'],
        'spare_part__part_number': ['exact', 'icontains'],
        'warehouse': ['exact'],
        'quantity_on_hand': ['gte', 'lte', 'exact'],
        'reorder_point': ['gte', 'lte', 'isnull'],
    }
    search_fields = ['spare_part__name', 'spare_part__part_number', 'warehouse__name', 'notes']

    @action(detail=True, methods=['post'], url_path='adjust-stock')
    @transaction.atomic
    def adjust_stock(self, request, pk=None):
        stock_item = self.get_object()
        try:
            adjustment = float(request.data.get('adjustment'))
        except (ValueError, TypeError):
            return Response({"error": "Valid 'adjustment' quantity not provided."}, status=status.HTTP_400_BAD_REQUEST)

        notes = request.data.get('notes', '')

        new_quantity = stock_item.quantity_on_hand + adjustment
        if new_quantity < 0:
            return Response(
                {"error": f"Adjustment would result in negative stock ({new_quantity}). Current stock: {stock_item.quantity_on_hand}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        stock_item.quantity_on_hand = new_quantity
        if notes: # Append adjustment notes to existing notes
            stock_item.notes = f"{stock_item.notes or ''}\nStock Adjustment ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {adjustment:+.2f}. Reason: {notes}".strip()
        else:
             stock_item.notes = f"{stock_item.notes or ''}\nStock Adjustment ({timezone.now().strftime('%Y-%m-%d %H:%M')}): {adjustment:+.2f}.".strip()


        stock_item.last_stocked_date = timezone.now()
        stock_item.save()

        return Response(self.get_serializer(stock_item).data)

class PartReservationViewSet(viewsets.ModelViewSet):
    queryset = PartReservation.objects.all().select_related('work_order', 'spare_part', 'spare_part__category').order_by('-reservation_date')
    serializer_class = PartReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'work_order': ['exact'],
        'spare_part': ['exact'],
        'is_fulfilled': ['exact'],
        'reservation_date': ['date__gte', 'date__lte', 'range'],
    }
    search_fields = ['work_order__title', 'spare_part__name', 'notes']

    @action(detail=True, methods=['post'], url_path='fulfill')
    @transaction.atomic
    def fulfill_reservation(self, request, pk=None):
        reservation = self.get_object()
        if reservation.is_fulfilled:
            return Response({"message": "Reservation already fulfilled."}, status=status.HTTP_400_BAD_REQUEST)

        # This assumes fulfillment happens from a "general" stock or the specific warehouse logic is simple/implicit.
        # For multi-warehouse, you'd need to specify which warehouse to fulfill from.
        try:
            # For simplicity, let's assume we fulfill from any warehouse that has the part.
            # A real system would need warehouse selection.
            stock_item = StockItem.objects.select_for_update().get(
                spare_part=reservation.spare_part,
                quantity_on_hand__gte=reservation.quantity_reserved
                # Add warehouse filter here if applicable: warehouse=target_warehouse
            )
        except StockItem.DoesNotExist:
            return Response(
                {"error": f"Not enough stock for {reservation.spare_part.name} or part not found in any suitable warehouse."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except StockItem.MultipleObjectsReturned:
             # If multiple stock items match (e.g. in different warehouses), need a strategy.
             # Picking the one with most stock as a simple strategy:
            stock_item = StockItem.objects.select_for_update().filter(
                spare_part=reservation.spare_part,
                quantity_on_hand__gte=reservation.quantity_reserved
            ).order_by('-quantity_on_hand').first()
            if not stock_item: # Should not happen if DoesNotExist was not caught before, but defensive
                 return Response({"error": "Error selecting stock item among multiples."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        stock_item.quantity_on_hand -= reservation.quantity_reserved
        stock_item.last_stocked_date = timezone.now() # Or last issued date
        stock_item.save()

        reservation.is_fulfilled = True
        reservation.fulfilled_date = timezone.now()
        reservation.save()

        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=['post'], url_path='unfulfill')
    @transaction.atomic
    def unfulfill_reservation(self, request, pk=None):
        reservation = self.get_object()
        if not reservation.is_fulfilled:
            return Response({"message": "Reservation is not fulfilled, cannot unfulfill."}, status=status.HTTP_400_BAD_REQUEST)

        # When unfulfilling, we need to return parts to stock.
        # Again, warehouse logic is simplified here.
        try:
            # Try to find any stock item for this part to return to.
            # A more robust system might track which warehouse it came from.
            stock_item = StockItem.objects.select_for_update().filter(spare_part=reservation.spare_part).first()
            if not stock_item:
                # If no stock item exists, this is problematic. Should it create one?
                # For now, error out or log, as this implies data inconsistency.
                # This could happen if the part was deleted from all warehouses after fulfillment.
                return Response({"error": f"Cannot find a stock item for {reservation.spare_part.name} to return parts to. Manual adjustment needed."}, status=status.HTTP_400_BAD_REQUEST)

            stock_item.quantity_on_hand += reservation.quantity_reserved
            stock_item.last_stocked_date = timezone.now() # Or last returned date
            stock_item.save()
        except IntegrityError as e: # Should not happen with .first() but defensive
            return Response({"error": f"Database error during stock return: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        reservation.is_fulfilled = False
        reservation.fulfilled_date = None
        reservation.save()
        return Response(self.get_serializer(reservation).data)
