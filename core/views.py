from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
import io
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from core.filters import *
import os
from django.views.generic import View
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
            return User.objects.filter(id=user.id)
        return User.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        generate_pdf = request.query_params.get(
            'generate_pdf', 'false').lower() == 'true'
        if generate_pdf:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.setFont("Helvetica", 12)
            width, height = letter

            y = height - 40  # Start from the top of the page

            users = self.get_queryset()
            p.drawString(30, y, "User List")
            y -= 20

            for user in users:
                p.drawString(
                    30, y, f"First Name: {user.first_name}, Last Name: {user.last_name}, Email: {user.email}, User Type: {user.user_type}")
                y -= 20
                if y < 40:
                    p.showPage()
                    p.setFont("Helvetica", 12)
                    y = height - 40

            p.save()

            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename='user_list.pdf')

        return response


class PDFView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        user = request.user

        users = User.objects.all() if user.is_superuser else None

        serializer = UserSerializer(
            users, many=True, context={'request': request})
        context = {'users': serializer.data}

        html_string = render_to_string('user_list.html', context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=user_list.pdf'

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
        if not pdf.err:
            response.write(result.getvalue())
            return response
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')


class GetAllTherepistsViewset(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(user_type='therapist')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


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
        print(user)
        if not user.is_superuser:
            transaction = Transaction.objects.filter(user=user.id)
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


# Working with youTube API to get videos on mental health
class VideosView(APIView):
    def get(self, request):
        api_service_name = "youtube"
        api_version = "v3"
        api_key = settings.API_KEY

        youtube = build(api_service_name, api_version, developerKey=api_key)

        search_queries = ["mental health",
                          "calming music", "Podcast mental health"]
        videos = []

        for query in search_queries:
            youtube_request = youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=20
            )
            response = youtube_request.execute()
            videos.extend(response['items'])

        video_data = []
        for video in videos:
            video_info = {
                "title": video["snippet"]["title"],
                "description": video["snippet"]["description"],
                "channelTitle": video["snippet"]["channelTitle"],
                "publishTime": video["snippet"]["publishTime"],
                "videoId": video["id"]["videoId"],
                "URL": f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            }
            video_data.append(video_info)

        return Response(video_data, status=status.HTTP_200_OK)
