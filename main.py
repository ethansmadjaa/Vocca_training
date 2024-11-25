import insert_event, get_ten_events


def main():
    print('What do you want to do?')
    choice = input("1. Insert an event\n2. Get the ten upcoming events\n3. Insert a test event\n")

    if choice == '1':
        summary = input("Enter event summary: ")
        location = input("Enter event location: ")
        description = input("Enter event description: ")
        start_date = input("Enter event start date (YYYY-MM-DD): ")
        start_time = input("Enter event start time (HH:MM): ")
        start = start_date + 'T' + start_time + ':00'
        end_date = input("Enter event end date (YYYY-MM-DD): ")
        end_time = input("Enter event end time (HH:MM): ")
        end = end_date + 'T' + end_time + ':00'
        print('Start date:' + str(start) + '\nEnd date:' + str(end))
        print('Inserting an event')
        insert_event.insert_event(
            summary=summary,
            location=location,
            description=description,
            start=start,
            end=end,
        )
    elif choice == '2':
        get_ten_events.get_ten_events()
    elif choice == '3':
        insert_event.insert_event_test()
    else:
        print('Invalid choice. Please select 1, 2 or 3 .')


if __name__ == '__main__':
    main()
