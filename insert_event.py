from googleapiclient.discovery import build
from google.api_core import retry
from googleapiclient.errors import HttpError

import credentials


async def insert_event(summary, location, description, start, end):
    """Inserts an event into the user's primary Google Calendar."""
    creds = credentials.get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start,
            'timeZone': 'Europe/Paris',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'Europe/Paris',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f'Event created successfully: {event.get("htmlLink")}')
        return event
    except HttpError as e:
        if e.resp.status == 409:
            print('Conflict: This time slot is already booked')
            raise ValueError("This time slot is already booked")
        elif e.resp.status == 403:
            print('Permission denied: Please check calendar access')
            raise ValueError("Calendar access error")
        else:
            print(f'An error occurred: {e}')
            raise
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        raise


def insert_event_test():
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
    }

    try:
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % (event_result.get('htmlLink')))
    except Exception as e:
        print(f'An error occurred: {e}')
