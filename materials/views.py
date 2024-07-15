from rest_framework import viewsets, permissions

from .serializers import MaterialSerializer
from .models import Material

class MaterialViewset(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MaterialSerializer
    queryset = Material.objects.all()