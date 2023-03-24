import caldav


class Calendariser:
    def __init__(self, url: str, username: str, password: str):
        client = caldav.DAVClient(url=url, username=username, password=password)

        principal = client.principal()
        calendars = principal.calendars()
        if calendars:
            print("your principal has %i calendars:" % len(calendars))
            for c in calendars:
                print("    Name: %-20s  URL: %s" % (c.name, c.url))

    def add_to_calendar(self) -> None:
        pass
