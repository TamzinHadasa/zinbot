"""Wraps mwclient in interacting with the MW API."""
from typing import Any, Literal

from mwclient import Site  # type:ignore[import-untyped]
from mwclient.page import Page  # type:ignore[import-untyped]

from classes import ZBError, Namespace, User
import config
import constants
import logging_


Queue = list[dict[str, Any]]


_site = Site('en.wikipedia.org',
             clients_useragent=constants.USER_AGENT,
             consumer_token=config.CONSUMER_TOKEN,
             consumer_secret=config.CONSUMER_SECRET,
             access_token=config.ACCESS_TOKEN,
             access_secret=config.ACCESS_SECRET)
RequestParams = dict[str, object]
ResponseJSON = dict[str, 'ResponseJSON'] | list['ResponseJSON']
TokenType = Literal[
    'createaccount', 'csrf', 'deleteglobalaccount', 'login', 'patrol',
    'rollback', 'setglobalaccountstatus', 'userrights', 'watch'
]


class PageNotFoundError(ZBError):
    """Exception raised by `get_page` when a page does not exist."""


def get_page(title: str, ns: int = 0, must_exist: bool = False) -> Page:
    """Wrapper for mwclient.page.Page(), with optional existence check.

    Does not guarantee that page actually exists; check with .exists().

    Args:
      title:  A str matching a valid wikipage title.
      ns:  An int of the MW-defined number for the page's namespace.

    Returns:
      A Page with title `title` in namespace with number `ns`, possibly
      nonexistent (if not `must_exist`).

    Raises:
      PageNotFoundError:  If `must_exist` but the page does not exist.
    """
    page = Page(_site,
                name=f"{Namespace(ns).prefix}{title}".removeprefix(":"))
    if must_exist and not page.exists:
        raise PageNotFoundError("Page does not exist")
    return page


def get_user(username: str) -> User:
    return _site.users(users=username, prop='groups')


def buildqueue(showdeleted: str = "", start: int = 1) -> Queue:
    """Build a NewPagesFeed queue of unreviewed pages in the mainspace.

    Args:
      show:  A list containing any of the following: 'showredirs',
        'showdeleted', and 'showothers'.  These will be set to boolean 1
        in the queue's parameters.  (N.B.:  'showdeleted' means
        "nominated for deletion", not "deleted".)  Setting none of these
        is the same as setting all of them.
      start:  A timestamp to start at, in a format accepted by the MW
        API.  NOTE:  Setting to 0 throws an error with the API.

    Returns:
      A list of dicts, potentially empty, based on on the 'pages' field
      of the JSON returned by the API.
    """
    queue: Queue = _site.api(action='pagetriagelist',
                             namespace=Namespace.MAIN,
                             showunreviewed=True,
                             dir='oldestfirst',
                             limit=200,
                             date_range_from=start,
                             showdeleted=showdeleted)['pagetriagelist']['pages']
    return queue


def review(page: Page) -> None:
    """Review a page using PageTriage.

    Arg:
      page:  A Page representing a wikipage to review.
    """
    _site.api(action='pagetriageaction',
              pageid=page.pageid,
              reviewed=1,
              skipnotif=True,
              token=_site.get_token('csrf'))
    print(f"Reviewed {page.page_title}")
