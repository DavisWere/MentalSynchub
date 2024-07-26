from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import (
    CustomObtainTokenPairView,
    UserViewSet,
    BookingSessionViewSet,
    TransactionViewSet,
    ConfirmPaymentStatusApiView,
    CreateEventView,
    ScheduleViewSet,
    VideosView,
    GetAllTherepistsViewset
)


core_router = DefaultRouter()
core_router.register(r"user", UserViewSet)
core_router.register(r'therapists', GetAllTherepistsViewset)
core_router.register(r"booking-session", BookingSessionViewSet)
core_router.register(r"transaction", TransactionViewSet)
core_router.register(r"schedules", ScheduleViewSet, basename='schedules')


urlpatterns = [
    path("token/request/", CustomObtainTokenPairView.as_view(), name="token_request"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "confirm-payment-status/<int:transaction_id>/", ConfirmPaymentStatusApiView.as_view(),
    ),

    path('create-event/', CreateEventView.as_view(), name='create-event'),
    path('youtube/', VideosView.as_view(), name='youtube'),


]
urlpatterns += core_router.urls
