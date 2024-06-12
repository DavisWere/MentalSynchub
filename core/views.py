from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build



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
                         Transaction, Game, ChatCompletion, Schedule)
from core.serializers import (CustomTokenObtainPairSerializer, ChatCompletionSerializer,
                              UserSerializer, BookingSessionSerializer, GameSerializer, TransactionSerializer, ConfirmPaymentStatusSerializer, ScheduleSerializer)


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

    # def get_queryset(self):
    #     user = self.request.user
    #     print(user)
    #     all_transactions = Transaction.objects.filter(user=user)
    #     return all_transactions
    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser:
            transaction = Transaction.objects.filter(user=user)
        else:
            transaction = Transaction.objects.all()
        return transaction


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


class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Schedule.objects.filter(user=self.request.user)



class CreateEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_credentials(self):
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', settings.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', settings.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def post(self, request, *args, **kwargs):
        attendees = request.data.get('attendees')
        reminders = int(request.data.get('reminders', 10))
        start_time = request.data.get('start_date')
        end_time = request.data.get('end_date')
        time_zone = request.data.get('time_zone', 'UTC')

        try:
            creds = self.get_credentials()
            service = build('calendar', 'v3', credentials=creds)

            event = {
                'summary': 'Sample Meeting',
                'location': '',
                'description': 'A chance to hear more about Google Meet API and Google Calendar API.',
                'start': {
                    'dateTime': start_time,
                    'timeZone': time_zone,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': time_zone,
                },
                'conferenceData': {
                    'createRequest': {
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        },
                        'requestId': 'some-random-string'
                    }
                },
                'attendees': [{'email': email.strip()} for email in attendees.split(',')],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': reminders},
                    ],
                },
            }

            event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
            event_created = event.get("htmlLink")
            meeting_link = event["conferenceData"]["entryPoints"][0]["uri"]

            Schedule.objects.create(
                user=request.user,
                link=meeting_link,
                attendees=attendees,
                reminders=reminders,
                start_time=start_time,
                end_time=end_time,
            )
            return Response({
                'event_link': event_created,
                'meet_link': meeting_link,
                'post_data': request.data
            }, status=status.HTTP_201_CREATED)

        # except HttpError as error:
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
