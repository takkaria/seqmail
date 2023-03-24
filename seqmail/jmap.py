import dataclasses
import json
from typing import Any

import requests
import typedload

Mailbox = dict[str, Any]


@dataclasses.dataclass
class Attachment:
    blob_id: str = dataclasses.field(metadata={"name": "blobId"})
    charset: str
    cid: str
    disposition: str
    language: str
    location: str
    name: str
    part_id: str = dataclasses.field(metadata={"name": "partId"})
    size: int
    type: str


@dataclasses.dataclass
class From:
    email: str
    name: str


@dataclasses.dataclass
class Email:
    attachments: list[Attachment]
    addr_from: list[From] = dataclasses.field(metadata={"name": "from"})
    unsubscribe_urls: list[str] | None = dataclasses.field(
        metadata={"name": "header:List-Unsubscribe:asURLs"}
    )
    id: str
    preview: str
    received_at: str = dataclasses.field(metadata={"name": "receivedAt"})
    subject: str
    thread_id: str = dataclasses.field(metadata={"name": "threadId"})


class JMAPClient:
    """The tiniest JMAP client you can imagine."""

    def __init__(self, hostname: str, token: str) -> None:
        """Initialize using a hostname, username and password"""
        self.hostname = hostname
        self.token = token
        self.session = None
        self.api_url = None
        self.account_id = None
        self.mailboxes = None

    def get_session(self):
        """Return the JMAP Session Resource as a Python dict"""
        if self.session:
            return self.session

        r = requests.get(
            "https://" + self.hostname + "/.well-known/jmap",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5,
        )
        r.raise_for_status()
        self.session = r.json()
        self.api_url = self.session["apiUrl"]
        return self.session

    def get_account_id(self) -> str:
        """Return the accountId for the account matching self.username"""
        if self.account_id:
            return self.account_id

        session = self.get_session()

        account_id = session["primaryAccounts"]["urn:ietf:params:jmap:mail"]
        self.account_id = account_id
        return account_id

    def call(self, call) -> Any:
        if not self.api_url:
            raise ValueError("No session defined")

        """Make a JMAP POST request to the API, returning the reponse as a
        Python data structure."""
        res = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(call),
            timeout=5,
        )
        res.raise_for_status()
        return res.json()

    def get_mailboxes(self) -> list[Mailbox]:
        if self.mailboxes:
            return self.mailboxes

        response = self.call(
            {
                "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                "methodCalls": [
                    [
                        "Mailbox/get",
                        {
                            "accountId": self.get_account_id(),
                        },
                        "a",
                    ]
                ],
            }
        )

        self.mailboxes = response["methodResponses"][0][1]["list"]
        return self.mailboxes

    def move_message(self, email_id: str, folder_id: str) -> None:
        response = self.call(
            {
                "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                "methodCalls": [
                    [
                        "Email/set",
                        {
                            "accountId": self.get_account_id(),
                            "update": {
                                email_id: {
                                    "mailboxIds": {folder_id: True},
                                }
                            },
                        },
                        "a",
                    ]
                ],
            }
        )
        if response["methodResponses"][0][0] == "error":
            raise ValueError("Couldn't move message")

    def get_emails(self, mailbox_id: str) -> list[Email]:
        result = self.call(
            {
                "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                "methodCalls": [
                    [
                        "Email/query",
                        {
                            "accountId": self.get_account_id(),
                            "filter": {"inMailbox": mailbox_id},
                            "sort": [{"property": "receivedAt", "isAscending": False}],
                        },
                        "a",
                    ],
                    [
                        "Email/get",
                        {
                            "accountId": self.get_account_id(),
                            "#ids": {
                                "resultOf": "a",
                                "name": "Email/query",
                                "path": "/ids/*",
                            },
                            "properties": [
                                "from",
                                "threadId",
                                "subject",
                                "receivedAt",
                                "preview",
                                "header:List-Unsubscribe:asURLs",
                                "attachments",
                            ],
                        },
                        "b",
                    ],
                ],
            }
        )

        return typedload.load(result["methodResponses"][1][1]["list"], list[Email])
