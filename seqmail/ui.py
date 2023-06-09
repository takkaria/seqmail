import sys
import webbrowser
from dataclasses import dataclass
from enum import Enum
from typing import Literal, NamedTuple, NoReturn

from colors import color
from simple_term_menu import TerminalMenu

from . import jmap, todoist
from .settings import SETTINGS


class ActionDescriptor(NamedTuple):
    key: str
    text: str


class ActionTypes(Enum):
    SKIP = ActionDescriptor("s", "Skip")
    DELETE = ActionDescriptor("d", "Delete")
    MARK_READ = ActionDescriptor("m", "Mark as read")
    ADD_TODO = ActionDescriptor("t", "Make todo...")
    FILE = ActionDescriptor("f", "File under...")
    UNSUBSCRIBE = ActionDescriptor("u", "Unsubscribe...")
    OPEN = ActionDescriptor("o", "Open in browser...")


def _actions_for_email(email: jmap.Email) -> list[ActionTypes]:
    options = set(ActionTypes)

    if email.unsubscribe_urls is None:
        options = options - {ActionTypes.UNSUBSCRIBE}

    return list(options)


def _choose_action(email: jmap.Email) -> ActionTypes | None:
    actions = _actions_for_email(email)
    options = [f"[{opt.value.key}] {opt.value.text}" for opt in actions]
    menu = TerminalMenu(options, title="What do you want to do?")
    index = menu.show()
    if index is None:
        return None
    else:
        return actions[index] or None


def _display_name(mailbox: jmap.Mailbox) -> str:
    shortcuts = {
        "Spam": "s",
        "Archive": "a",
        "Trash": "t",
        "Delete after 1 year": "1",
        "Receipts": "r",
        "Make filter": "f",
    }
    name = mailbox.name
    if name in shortcuts:
        return f"[{shortcuts[name]}] {name}"
    else:
        return name


def _choose_mailbox(client: jmap.JMAPClient) -> str | None:
    mailboxes = client.get_mailboxes()

    options = [_display_name(mailbox) for mailbox in mailboxes]
    menu = TerminalMenu(options, title="File where? (Press Esc to go back)")
    index = menu.show()
    if index is None:
        return None
    else:
        print(mailboxes[index].name)
        return mailboxes[index].id or None


def _make_url(id_: str, thread_id: str) -> str:
    return f"https://www.fastmail.com/mail/Inbox/{thread_id}.{id_}"


def _grey(text: str) -> str:
    result: str = color(text, fg=242)
    return result


def _display_email(email: jmap.Email) -> None:
    from_ = f"{email.addr_from[0].name} <{email.addr_from[0].email}>"

    print(_grey("Received: " + email.received_at))
    print(_grey("From:     ") + from_)
    print(_grey("Subject:  ") + email.subject)
    print()
    print("    " + "\n    ".join(email.preview.split("\n")))
    print()

    for ical in [a for a in email.attachments if a.type == "text/calendar"]:
        print(f"ical attachment: {ical.name}")
        print()


@dataclass
class AddTodo:
    text: str

    def run(self, _client: jmap.JMAPClient, email: jmap.Email) -> Literal[False]:
        email_url = _make_url(id_=email.id, thread_id=email.thread_id)
        todoist.add_todo(text=self.text, note=email_url)
        return False


class Skip:
    def run(self, _jmap_client: jmap.JMAPClient, _email: jmap.Email) -> Literal[True]:
        return True


@dataclass
class File:
    mailbox_id: str

    def run(self, jmap_client: jmap.JMAPClient, email: jmap.Email) -> bool:
        jmap_client.move_message(email.id, self.mailbox_id)
        return True


class Unsubscribe:
    def run(self, _jmap_client: jmap.JMAPClient, email: jmap.Email) -> Literal[False]:
        if not email.unsubscribe_urls:
            raise ValueError("Unsubscribe action called but no links to follow")

        found_url = None
        for url in email.unsubscribe_urls:
            if url.startswith("https://"):
                found_url = url
                break

        if found_url:
            browser = webbrowser.get("safari")
            browser.open_new_tab(found_url)

        return False


class Open:
    def run(self, _jmap_client: jmap.JMAPClient, email: jmap.Email) -> Literal[False]:
        url = _make_url(id_=email.id, thread_id=email.thread_id)
        browser = webbrowser.get("safari")
        browser.open_new_tab(url)
        return False


class Quit:
    def run(self, _jmap_client: jmap.JMAPClient, _email: jmap.Email) -> NoReturn:
        print("Quitting.")
        sys.exit(0)


Action = AddTodo | Skip | File | Unsubscribe | Open | Quit


def _choose_action_for_email(email: jmap.Email, jmap_client: jmap.JMAPClient) -> Action:
    selected = _choose_action(email)

    if selected is ActionTypes.ADD_TODO:
        print("What do you need to do? (Leave empty to abort)")
        text = input("> ")
        if text == "":
            return _choose_action_for_email(email, jmap_client)
        else:
            return AddTodo(text)
    elif selected is ActionTypes.SKIP:
        return Skip()
    elif selected is ActionTypes.FILE:
        mailbox_id = _choose_mailbox(jmap_client)
        if mailbox_id:
            return File(mailbox_id)
    elif selected is ActionTypes.UNSUBSCRIBE:
        return Unsubscribe()
    elif selected is ActionTypes.DELETE:
        return File(_find_mailbox_id(jmap_client, "Trash"))
    elif selected is ActionTypes.OPEN:
        return Open()

    return Quit()


def _process_action(jmap: jmap.JMAPClient, email: jmap.Email, action: Action) -> bool:
    print(f"Action selected: {action}")
    return action.run(jmap, email)


def _find_mailbox_id(jmap_client: jmap.JMAPClient, name: str) -> str:
    mailboxes = jmap_client.get_mailboxes()
    mailbox_id = [m for m in mailboxes if m.name == name][0].id
    return mailbox_id


def run() -> None:
    jmap_client = jmap.JMAPClient(
        hostname=SETTINGS.jmap.hostname, token=SETTINGS.jmap.token
    )
    inbox_id = _find_mailbox_id(jmap_client, "Inbox")

    result = jmap_client.get_emails(inbox_id)
    for email in result:
        _display_email(email)

        completed = False
        while not completed:
            action = _choose_action_for_email(email, jmap_client)
            completed = _process_action(jmap_client, email, action)

        print()
        print(color("====================================================", fg=234))
        print()
