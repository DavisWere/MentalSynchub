from rest_framework import serializers

from games.models import Game

class GameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        fields = ['id', 'user', 'player_choice', 'computer_choice',
                  'play_again', 'result', 'created_at']
        read_only_fields = ['created_at', 'user', 'result', 'computer_choice']

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")

        user = request.user
        game = object.create(**validated_data)
        return game

