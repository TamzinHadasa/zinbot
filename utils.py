"""Utility functions."""
import datetime as dt
from enum import Enum, IntEnum
import json
import urllib.parse
from typing import Any, Optional, TypedDict

from pywikibot import Page, Timestamp

import constants
import api

LoggerData = dict[str, list['Event']]


class ZBError(Exception):
    """Generic exception for errors specific to 'zinbot's behavior."""


class Event(TypedDict):
    """Structure of a logged event"""
    page: str
    code: str
    message: str
    timestamp: str


class Namespace(IntEnum):
    """Enum holding both number and namespace prefix.

    Attributes:
      number:  An int of a namespace number.
      prefix:  A str of a namespace prefix, including trailing colon.
    """
    def __new__(cls, number: int, _name: Optional[str] = None) -> 'Namespace':
        """Constructs a Namespace instance with an int value.

        Args:
          number:  An int of a namespace number.
          _name:  Used in `__init__`.
        """
        obj = int.__new__(cls, number)
        obj._value_ = number
        return obj

    def __init__(self, _number: int, name: Optional[str] = None) -> None:  # pylint: disable=super-init-not-called
        """Initalizes a Namespace instance.

        Args:
          _number:  Used in `__new__` to set value.
          name:  None (default) or a str of a namespace prefix.  If
            None, a first-letter-capitalized version of the variable
            name will be used.
        """
        raw_prefix = name if name is not None else self.name.capitalize()
        self.prefix = raw_prefix + ":"
        # Can't dynamically create new Namespace objects.
        self.talk = self + 1 if self >= 0 else None
        self.talkprefix = raw_prefix + ' talk:' if self >= 0 else None

    def __str__(self) -> str:
        """Give a string of the value, to allow passing to URLs."""
        return str(self.value)

    MAIN = 0, ''
    USER = 2
    PROJECT = 4
    FILE = 6
    MEDIAWIKI = 8, 'MediaWiki'
    TEMPLATE = 10
    HELP = 12
    CATEGORY = 14
    PORTAL = 100
    DRAFT = 118
    TIMEDTEXT = 710, 'TimedText'
    GADGET = 2300
    GADGET_DEFINITION = 2302, 'Gadget definition'
    SPECIAL = -1
    MEDIA = -2


class Title(str):
    """The title of a MediaWiki page, with access to namespace number.

    Attributes:
      namespace:  A Namespace.
      basepage:  A str of the basepage component.
      subpage:  A str of the subpage component.
      as_url:  A str of the Title in URL-compatible format.
    """
    @staticmethod
    def from_page(page: Page) -> 'Title':
        """Create a Title based on a pywikibot.Page.

        Args:
          page:  A pywikibot.Page.

        Returns:
          A Title drawn from the page's title and namespace ID.
        """
        return Title(Namespace(page.namespace().id), page.title())

    def __new__(cls, namespace: Namespace, pagename: str) -> 'Title':
        """Construct a Title.

        Args:
          See `__init__`."""
        return super().__new__(cls, namespace.prefix + pagename)

    def __init__(self, namespace: Namespace, pagename: str) -> None:
        """Initialize a Title.

        Args:
          namespace:  A Namespace.
          basepage:  A str of a basepage name.
          subpage:  A str of a subpage name.
        """
        super().__init__()
        self.namespace = namespace
        self.pagename = pagename
        self.as_url = urllib.parse.quote(self)


class OnWikiLogger:
    """Controls on-wiki logging of events."""
    _dateformat = "%Y-%m-%d"
    _timestampformat = "%H:%M:%S %Y-%m-%d (UTC)"

    def __init__(
        self,
        logpage: str,
        ns_and_basepage: tuple[Namespace, str] = (Namespace.USER,
                                                  "Tamzin/logs/")
    ) -> None:
        """Initialize an OnWikiLogger.

        Args:
          logpage:  A str of a subpage name.
          ns_and_basepage:  A tuple of a Namespace and a str of a basepage
            name.
        """
        self._logpage = logpage
        self._ns_and_basepage = ns_and_basepage
        self._logtitle = Title(ns_and_basepage[0],
                               ns_and_basepage[1] + logpage)

    def __repr__(self) -> str:
        return f"Logger({self._logpage}, {self._ns_and_basepage})"

    def _load_json(self) -> LoggerData:
        return json.loads(api.get_page(self._logtitle.pagename,
                                       self._logtitle.namespace).text)

    def _save_json(self, data: LoggerData, summary: str) -> None:
        api.post({'action': 'edit',
                  'title': self._logtitle,
                  'text': json.dumps(data),
                  'summary': summary})

    def _is_too_old(self, timestamp: str) -> bool:
        return (api.site_time().date()
                - dt.datetime.strptime(timestamp, self._dateformat).date()
                > dt.timedelta(days=7))

    def log(self,
            message: Enum,
            page: str,
            timestamp: Timestamp,
            **formatters: Any) -> None:
        """Log an event.

        Arg:
          message:  An Enum, the name of which can serve as an error
            code and the value of which is an error message.
          page:  A str of a page's title, including leading colon for
            mainspace.
          timestamp:  A pywikibot.Timestamp.
          **formatters:  Objects to pass to the Enum's value for
            formatting.
        """
        data = self._load_json()
        if page in [i['page'] for day in data.values() for i in day]:
            return  # Skip if already logged.
        event: Event = {'page': page,
                        'code': message.name,
                        'message': message.value.format(page=page,
                                                        **formatters),
                        'timestamp': timestamp.strftime(self._timestampformat)}
        now = api.site_time().strftime(self._dateformat)
        if now not in data:
            data[now] = []
        data[now].append(event)
        self._save_json(data, f"Logging [[{page}]] (code {message.name})")

    def cleanup(self) -> bool:
        """Remove old and resolved log entries.

        Returns:
          A bool indicating whether cleanup occurred.
        """
        data = self._load_json()
        newdata = {k: [i for i in v if not _is_reviewed(i['page'])]
                   for k, v in data.items() if v and not self._is_too_old(k)}
        if newdata != data:
            self._save_json(newdata, "Removing old and/or reviewed entries.")
            return True
        return False


# Probably shouldn't be in `utils` long-term but it's fine for now.
def _is_reviewed(page: str) -> bool:
    logs = api.get({'action': 'query',
                    'list': 'logevents',
                    'letitle': page,
                    'letype': 'pagetriage-curation'})['query']['logevents']
    for entry in logs:
        # Commented out till <https://github.com/python/mypy/pull/10191>
        # is done:
        # match entry['action']:
        #     case 'reviewed':
        #         return True
        #     case 'unreviewed':
        #         return False
        if entry['action'] == 'reviewed':
            return True
        if entry['action'] == 'unreviewed':
            return False
    return False


def log_local(title: Title, logfile: str) -> None:
    """Append a page's title and URL to a document in folder `logs/`.

    Args:
      title:  A str of a title that should be logged.
      logfile:  A file (extant or not) in folder `logs/`.
    """
    with open(f"logs/{logfile}", 'a', encoding='utf-8') as f:
        f.write(f"{title} <{constants.WIKI_URL}{title.as_url}>\n")
