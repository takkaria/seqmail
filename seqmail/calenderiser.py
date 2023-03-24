import caldav
from requests.auth import AuthBase


class OAuth(AuthBase):
    def __init__(self, credentials):
        self.credentials = credentials

    def __call__(self, r):
        self.credentials.apply(r.headers)
        return r


class Calendariser:
    def __init__(self, url: str, username: str, password: str):
        client = caldav.DAVClient(url=url, auth=OAuth((username, password)))

        principal = client.principal()
        calendars = principal.calendars()
        if calendars:
            print("your principal has %i calendars:" % len(calendars))
            for c in calendars:
                print("    Name: %-20s  URL: %s" % (c.name, c.url))

    def add_to_calendar():
        pass
