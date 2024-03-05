from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import CustomObtainTokenPairView, UserViewSet, BookingSessionViewSet, TransactionViewSet , GameView


core_router = DefaultRouter()
core_router.register(r"user",UserViewSet)
core_router.register(r"booking-session", BookingSessionViewSet)
core_router.register(r"transaction", TransactionViewSet)

url_patterns = core_router.urls
url_patterns += [
    path("token/request/", CustomObtainTokenPairView.as_view(), name="token_request"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('play-game/', GameView.as_view(), name='play-game'),
    
   
   

]