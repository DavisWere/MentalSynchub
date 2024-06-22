from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from core.filters import *
import os
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.response import Response
from django.views import View
from rest_framework_simplejwt.views import TokenObtainPairView
from core.models import (User, BookingSession,
                         Transaction, ChatCompletion, Schedule)
from core.serializers import (CustomTokenObtainPairSerializer, ChatCompletionSerializer,
                              UserSerializer, BookingSessionSerializer, TransactionSerializer, ConfirmPaymentStatusSerializer, ScheduleSerializer)


class CustomObtainTokenPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

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
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

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
            creds = Credentials.from_authorized_user_file(
                'token.json', settings.SCOPES)
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

            event = service.events().insert(calendarId='primary', body=event,
                                            conferenceDataVersion=1).execute()
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
