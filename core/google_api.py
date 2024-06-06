from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings
import os
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_credentials():
    creds = None
    token_path = 'token.json'
    if os.path.exists(token_path):
        with open(token_path, 'r') as token:
            creds_data = json.load(token)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                settings.GOOGLE_CLIENT_SECRET_JSON,
                scopes=SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            print(f'Please go to this URL: {authorization_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def create_google_meet_event(summary, start_time, end_time, attendees=[]):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
        'attendees': [{'email': email} for email in attendees],
        'conferenceData': {
            'createRequest': {
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                },
                'requestId': 'randomString'
            }
        },
    }

    event = service.events().insert(calendarId='primary', body=event,
                                    conferenceDataVersion=1).execute()
    return event
