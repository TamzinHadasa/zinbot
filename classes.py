"""Utility functions."""
from enum import IntEnum
import urllib.parse
from typing import Any, Optional, TypeVar, TypedDict

from pywikibot import Page

T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')


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


class SensitivityMixin:  # pylint: disable=too-few-public-methods
    """Make object aware of whether it or its members have been changed."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._changed = False
        try:
            self._contents = self.values()  # type: ignore
        except AttributeError:
            self._contents = self
        super().__init__(*args, **kwargs)  # type: ignore

    def been_changed(self) -> bool:
        """See if object or its members have been changed."""
        return (any(getattr(i, 'been_changed', lambda: False)()
                    for i in self._contents)
                or self._changed)


class SensitiveDict(SensitivityMixin, dict[KT, VT]):
    """Dict that knows whether it's been updated since initialization."""

    def __setitem__(self, k: KT, v: VT) -> None:
        self._changed = True
        return super().__setitem__(k, v)

    def __delitem__(self, v: KT) -> None:
        self._changed = True
        return super().__delitem__(v)


class SensitiveList(SensitivityMixin, list[Any]):
    """List that knows whether it's been updated since initialization."""

    def append(self, item: object) -> None:
        self._changed = True
        super().append(item)
