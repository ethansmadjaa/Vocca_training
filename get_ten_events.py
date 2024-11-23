from __future__ import print_function

from datetime import datetime, timezone

from googleapiclient.discovery import build

import credentials


def get_ten_events():
    """
        Shows basic usage of the Google Calendar API.
    Lists the next 10 events on the user's primary calendar.
    """
    creds = credentials.get_credentials()

    try:
        # Build the service object.
        service = build('calendar', 'v3', credentials=creds)

        # Get the current time in UTC.
        now = datetime.now(timezone.utc).isoformat()

        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Print the start time and summary of each event.
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"{start}: {event.get('summary', 'No Title')}")
    except Exception as e:
        print(f'An error occurred: {e}')
