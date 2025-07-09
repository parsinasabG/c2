from rest_framework import viewsets, permissions
from .models import Asset
from .serializers import AssetSerializer

class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.
    """
    queryset = Asset.objects.all().order_by('-created_at')
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated] # Or more specific permissions

    # Optional: You can add custom actions or override methods here
    # For example, to implement more complex filtering or specific business logic

    # def get_queryset(self):
    #     """
    #     Optionally restricts the returned assets,
    #     for example by filtering for a user-specific company.
    #     """
    #     user = self.request.user
    #     # Example: return Asset.objects.filter(company=user.company)
    #     return Asset.objects.all().order_by('-created_at')

    # Example of a custom action:
    # from rest_framework.decorators import action
    # from rest_framework.response import Response
    # @action(detail=True, methods=['post'])
    # def perform_maintenance(self, request, pk=None):
    #     asset = self.get_object()
    #     # ... logic for performing maintenance ...
    #     return Response({'status': 'maintenance scheduled'})
