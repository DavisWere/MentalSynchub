from django.contrib import admin

from games.models import Game

class GameAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'player_choice',
        'computer_choice',
        'result',
        'play_again'
    ]

admin.site.register(Game, GameAdmin)

