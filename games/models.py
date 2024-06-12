from django.db import models
from core.models import User

class Game(models.Model):
    ROCK = 'rock'
    PAPER = 'paper'
    SCISSORS = 'scissors'

    CHOICES = [
        (ROCK, 'rock'),
        (PAPER, 'paper'),
        (SCISSORS, 'scissors'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Choices: rock, paper, scissors
    player_choice = models.CharField(max_length=10, choices=CHOICES)
    # Choices: rock, paper, scissors
    computer_choice = models.CharField(max_length=10)
    # Result of the game (e.g., "You Won!", "A Draw!", "You Lost!")
    result = models.CharField(max_length=20)
    play_again = models.BooleanField(default=True)
    # Timestamp when the game was played
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Game played by {self.user.username} at {self.created_at}"

