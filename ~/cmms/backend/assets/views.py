from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Asset
from .serializers import AssetSerializer

class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.
    Supports filtering by name, tag, model, location, and criticality.
    """
    queryset = Asset.objects.all().order_by('name')
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated] # Or more specific permissions as needed
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'name': ['icontains'],
        'tag': ['exact', 'icontains'],
        'model': ['icontains'],
        'location': ['icontains', 'exact'],
        'criticality': ['exact', 'in'],
        'installation_date': ['exact', 'year__gte', 'year__lte', 'range']
    }
    search_fields = ['name', 'tag', 'model', 'serial_number', 'location', 'description']

    # Example:
    # def get_queryset(self):
    #     """
    #     Optionally restricts the returned assets,
    #     for example by filtering for a user-specific company or department.
    #     """
    #     user = self.request.user
    #     # return Asset.objects.filter(company=user.company_profile.company)
    #     return Asset.objects.all().order_by('name')
