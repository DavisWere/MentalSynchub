from django.shortcuts import render
import calendar
from django.utils import timezone
import requests
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from django.http import JsonResponse
import random
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import os
from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.conf import settings
from rest_framework.response import Response
from django.views import View
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import (User, BookingSession,
                         Transaction, Game, ChatCompletion)
from core.serializers import (CustomTokenObtainPairSerializer, ChatCompletionSerializer,
                              UserSerializer, BookingSessionSerializer, GameSerializer, TransactionSerializer, ConfirmPaymentStatusSerializer)


class CustomObtainTokenPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser:
            user = User.objects.filter(user=user)
        else:
            user = User.objects.all()
        return user

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(pk=user.pk)
        return queryset


class BookingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSessionSerializer
    queryset = BookingSession.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        all_booked_sessions = BookingSession.objects.filter(user=user)
        return all_booked_sessions


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(user)
        all_transactions = Transaction.objects.filter(user=user)
        return all_transactions


class ConfirmPaymentStatusApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Transaction.objects.all()

    def get(self, request, transaction_id, format=None):
        transaction = get_object_or_404(Transaction, pk=transaction_id)
        serializer = ConfirmPaymentStatusSerializer(instance=transaction)
        result = serializer.confirm_payment_status()

        return Response(TransactionSerializer(result).data)

    def get_queryset(self):
        user = self.request.user
        print(user)
        all_transactions = Transaction.objects.filter(user=user)
        return all_transactions


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


class ChatCompletion(View):
    queryset = ChatCompletion.objects.all()
    serializer_class = ChatCompletionSerializer
