from django.urls import path

from games.views import GameView

urlpatterns = [
    path('play-game/', GameView.as_view(), name='play-game'),
]
