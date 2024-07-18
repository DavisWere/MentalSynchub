from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MaterialViewset

router = DefaultRouter()

router.register(r'materials', MaterialViewset, basename='materials')
urlpatterns = router.urls