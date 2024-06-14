from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response

from games.models import Game
from games.serializers import GameSerializer
import random

class GameView(APIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        player_name = request.user.username
        if not player_name:
            return Response({'error': 'Player name is required'}, status=400)

        user_input = request.data.get('player_choice')
        if user_input not in ["rock", "paper", "scissors"]:
            return Response({'error': 'Invalid choice'}, status=400)

        computer_choice = random.choice(["rock", "paper", "scissors"])

        user_score, computer_score, result = self.determine_winner(
            user_input, computer_choice)

        # Create a new game instance
        game = Game.objects.create(
            user=request.user,
            player_choice=user_input,
            computer_choice=computer_choice,
            result=result
        )

        # If the user wants to play again, return the game result without calculating the total score
        play_again = request.data.get('play_again', False)
        if play_again:
            return Response({
                'player_name': player_name,
                'user_choice': user_input,
                'computer_choice': computer_choice,
                'result': result,
                'user_score': user_score,
                'computer_score': computer_score,
            })

        # If play_again is False, calculate the total score by summing up the scores of all games
        games = Game.objects.filter(user=request.user)
        total_user_score = sum(game.user_score for game in games)
        total_computer_score = sum(game.computer_score for game in games)

        # Return the total scores along with the last game result
        return Response({
            'player_name': player_name,
            'user_choice': user_input,
            'computer_choice': computer_choice,
            'result': result,
            'total_user_score': total_user_score,
            'total_computer_score': total_computer_score,
        })

    def determine_winner(self, user_input, computer_choice):
        if user_input == computer_choice:
            return 10, 10, "A Draw!"
        elif (user_input == "rock" and computer_choice == "scissors") or \
             (user_input == "paper" and computer_choice == "rock") or \
             (user_input == "scissors" and computer_choice == "paper"):
            return 20, 0, "You Won!"
        else:
            return 0, 20, "You lost!"

