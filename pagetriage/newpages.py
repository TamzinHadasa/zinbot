"""Functions for interacting with the NewPagesFeed."""
import time
from typing import Any, Literal

from pywikibot import Page

import api
from api import RequestParams
import utils
from pagetriage import rfd
from utils import Namespace, ZBError

Queue = list[dict[str, Any]]


def checkqueue() -> None:
    """Loop through NewPagesFeed, 200 items at a time.

    Uses `buildqueue`, set to 'showdeleted' mode.
    """
    queue = _buildqueue(['showdeleted'])
    # The practical limit on this is that, if there's some unforeseen
    # situation that can cause an infinite loop, the resulting HTTP 429
    # response would halt the bot as provided for in `api._request`.
    while True:
        for page in queue:
            page = api.get_page(page['title'])
            if rfd.check_rfd(page):
                print(f"MATCH on {page=}")
                _review(page)
            else:
                print(f"No match on {page=}")
        try:
            last: int = queue[-1]['creation_date']
        except KeyError as e:  # Unlikely to ever happen but...
            raise ZBError("No 'creation_date' on last entry") from e
        # Intentionally starts next queue on final timestamp, not 1 past
        # it, since timestamps are non-unique.  Repeating is harmless,
        # as long as we account for the fact that `newqueue` will thus
        # always have a length of at least 1.
        newqueue = _buildqueue(['showdeleted'], start=last)
        # In theroy would als cause a break if 200+ entries have the
        # same timestamp.  Yeah, that's fine.
        if not newqueue or queue[-1]['pageid'] == newqueue[-1]['pageid']:
            break
        queue = newqueue
        # Rate limit.  NOTE: Will have to move somewhere else if tasks
        # are added that don't run through `checkqueue`.
        time.sleep(10)
    print("Queue complete. Checking if log cleanup is necessary.")
    rfd.cleanup()


def _buildqueue(show: list[Literal['showredirs', 'showdeleted', 'showothers']],
                start: int = 1) -> Queue:
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
    params: RequestParams = ({'action': 'pagetriagelist',
                              'namespace': Namespace.MAIN,
                              'showunreviewed': True,
                              'dir': 'oldestreview',
                              'limit': 200,
                              'date_range_from': start}
                             | {i: True for i in show})
    queue: Queue = api.get(params)['pagetriagelist']['pages']
    return queue


def _review(page: Page) -> None:
    """Patrol a page using PageTriage.

    Arg:
      page:  A Page representing a wikipage to patrol.
    """
    page_title = page.title()
    api.post({'action': 'pagetriageaction',
              'pageid': page.pageid,
              'reviewed': 1,
              'skipnotif': True})  # May change based on community's feelings.
    print(f"Patrolled {page_title}")
    utils.log_local(page_title, "reviewedpages.txt")
