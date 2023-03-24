from .settings import SETTINGS
import sys
from typing import List, NamedTuple, Optional
from enum import Enum
from todoist import TodoistAPI
from simple_term_menu import TerminalMenu
from .jmap import JMAPClient
from colors import color
import webbrowser


class ActionDescriptor(NamedTuple):
    key: str
    text: str


class Action(Enum):
    MARK_READ = ActionDescriptor("m", "Mark as read")
    ADD_TODO = ActionDescriptor("t", "Make todo...")
    FILE = ActionDescriptor("f", "File under...")
    UNSUBSCRIBE = ActionDescriptor("u", "Unsubscribe...")
    SKIP = ActionDescriptor("s", "Skip")


class MainMenu:
    def __init__(self, email: dict):
        self.actions = self.actions_for_email(email)

    def choose(self) -> Optional[Action]:
        options = [self.text_for_action(opt) for opt in self.actions]
        menu = TerminalMenu(options, title="What do you want to do?")
        index = menu.show()
        if index is None:
            return None
        else:
            return self.actions[index]

    @staticmethod
    def text_for_action(action: Action) -> str:
        return f"[{action.value.key}] {action.value.text}"

    def actions_for_email(self, email: dict) -> List[Action]:
        options = set(Action)

        if email["header:List-Unsubscribe:asURLs"] is None:
            options = options - set([Action.UNSUBSCRIBE])

        return list(options)


def choose_mailbox(jmap: JMAPClient) -> Optional[str]:
    mailboxes = jmap.get_mailboxes()

    def name(mailbox):
        SHORTCUTS = {
            "Spam": "s",
            "Archive": "a",
            "Trash": "t",
            "Delete after 1 year": "1",
            "Receipts": "r",
            "Make filter": "f",
        }
        name = mailbox["name"]
        if name in SHORTCUTS:
            return f"[{SHORTCUTS[name]}] {name}"
        else:
            return name

    options = [name(mailbox) for mailbox in mailboxes]
    menu = TerminalMenu(options, title="File where? (Press Esc to go back)")
    index = menu.show()
    if index is None:
        return None
    else:
        print(mailboxes[index]["name"])
        return mailboxes[index]["id"]


def _make_url(id, threadId, **kwargs):
    return f"https://www.fastmail.com/mail/Inbox/{threadId}.{id}"


def _display_email(email):
    def _grey(text):
        return color(text, fg=242)

    from_ = f"{email['from'][0]['name']} <{email['from'][0]['email']}>"

    print(_grey("Received: " + email["receivedAt"]))
    print(_grey("From:     ") + from_)
    print(_grey("Subject:  ") + email["subject"])
    print()
    print("    " + "\n    ".join(email["preview"].split("\n")))
    print()
    print(f"View at {color(_make_url(**email), fg=26, style='underline')}")
    print()

    for ical in [a for a in email["attachments"] if a["type"] == "text/calendar"]:
        print(f"ical attachment: {ical['name']}")
        print()


def choose_action_for_email(email: dict, jmap: JMAPClient):
    _display_email(email)

    menu = MainMenu(email)
    while True:
        selected = menu.choose()

        if selected is Action.ADD_TODO:
            print("What do you need to do? (Leave empty to abort)")
            text = input("> ")
            if text == "":
                print("\nNo todo made.\n")
            else:
                # TODO(anna): doesn't work!
                todoist = TodoistAPI(SETTINGS.todoist.key)
                todoist.quick.add(text=text, note=_make_url(**email))
                todoist.commit()
        elif selected is Action.SKIP:
            break
        elif selected is Action.FILE:
            mailbox_id = choose_mailbox(jmap)
            if mailbox_id:
                jmap.move_message(email["id"], mailbox_id)
                break
        elif selected is Action.UNSUBSCRIBE:
            found_url = None
            for url in email["header:List-Unsubscribe:asURLs"]:
                if url.startswith("https://"):
                    found_url = url
                    break

            if found_url:
                browser = webbrowser.get("safari")
                browser.open_new_tab(found_url)

        elif selected is None:
            print("Quitting.")
            sys.exit(0)

    print(f"Action selected: {selected.value[1]}")
    print()
    print(color("====================================================", fg=234))
    print()


def _find_mailbox(mailboxes, name):
    mailbox = [m for m in mailboxes if m["name"] == name][0]["id"]
    return mailbox


def run():
    jmap = JMAPClient(hostname=SETTINGS.jmap.hostname, token=SETTINGS.jmap.token)
    mailboxes = jmap.get_mailboxes()
    inbox_id = _find_mailbox(mailboxes, "Inbox")

    result = jmap.get_emails(inbox_id)
    for email in result["methodResponses"][1][1]["list"]:
        choose_action_for_email(email, jmap)
