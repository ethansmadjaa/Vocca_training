from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

import credentials


def insert_event():
    """Inserts an event into the user's primary Google Calendar."""
    creds = credentials.get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    # Define the event details
    event = {
        'summary': 'Sample Event',
        'location': '123 Main St, Anytown, USA',
        'description': 'This is a sample event created via the Google Calendar API.',
        'start': {
            'dateTime': '2024-12-01T10:00:00',
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': '2024-12-01T12:00:00',
            'timeZone': 'America/New_York',
        },
        'attendees': [
            {'email': 'attendee1@example.com'},
            {'email': 'attendee2@example.com'},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    try:
        # Insert the event into the calendar
        event_result = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        print('Event created: %s' % (event_result.get('htmlLink')))
    except Exception as e:
        print(f'An error occurred: {e}')
