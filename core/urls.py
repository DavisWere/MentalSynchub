from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import CustomObtainTokenPairView, UserViewSet, BookingSessionViewSet, TransactionViewSet, \
    ConfirmPaymentStatusApiView, GameView, CreateEventView, ScheduleViewSet



core_router = DefaultRouter()
core_router.register(r"user", UserViewSet)
core_router.register(r"booking-session", BookingSessionViewSet)
core_router.register(r"transaction", TransactionViewSet)
core_router.register(r"schedules", ScheduleViewSet, basename='schedules')

url_patterns = core_router.urls
url_patterns += [
    path("token/request/", CustomObtainTokenPairView.as_view(), name="token_request"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('play-game/', GameView.as_view(), name='play-game'),
    path(
        "confirm-payment-status/<int:transaction_id>/", ConfirmPaymentStatusApiView.as_view(),
    ),

    path('create-event/', CreateEventView.as_view(), name='create-event'),

]
