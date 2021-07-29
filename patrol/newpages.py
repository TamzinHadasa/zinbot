"""Functions for interacting with the NewPagesFeed."""
from typing import Any, Literal

from pywikibot import Page

from utils import ZBError, zb, log_local
from patrol.rfd import check_rfd


def buildqueue(show: list[Literal['showredirs', 'showdeleted', 'showothers']],
               start: int = 1) -> list[dict[str, Any]]:
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
    queue: list[dict[str, Any]] = zb.get(
        {'action': 'pagetriagelist',
         'namespace': 0,  # Main
         'showunreviewed': True,
         'dir': 'oldestreview',
         'limit': 200,  # NOTE: Move to constant if referenced elsewhere.
         'date_range_from': start}
        | {i: True for i in show}
    )['pagetriagelist']['pages']
    return queue


def checkqueue() -> None:
    """Loop through NewPagesFeed, 200 items at a time.

    Uses buildqueue(), set to 'showdeleted' mode.
    """
    queue = buildqueue(['showdeleted'])
    # The practical limit on this is that, if there's some unforeseen
    # situation that can cause an infinite loop, the resulting HTTP 429
    # response would halt the bot as specifically provided for in
    # utils.api().
    while True:
        for page in queue:
            page = zb.getpage(page['title'])
            if check_rfd(page):
                print(f"MATCH on {page=}")
                patrol(page)
            else:
                print(f"No match on {page=}")
        try:
            last = queue[-1]['creation_date']
        except KeyError as e:  # Unlikely to ever happen but...
            raise ZBError("No 'creation_date' on last entry") from e
        # Intentionally starts next queue on final timestamp, not 1 past
        # it, since timestamps are non-unique.  Repeating is harmless,
        # as long as we account for the fact that newqueue will thus
        # always have a length of at least 1.
        newqueue = buildqueue(['showdeleted'], start=last)
        # Also would cause a break if 200+ entries have the same
        # timestamp, but a break probably makes sense there anyways,
        # because something would have to have gone horribly wrong.
        if queue[-1]["pageid"] == newqueue[-1]["pageid"]:
            break
        queue = newqueue
    print("Queue complete")


def patrol(page: Page) -> None:
    """Patrol a page using PageTriage.

    Arg:
      page:  A Page representing a wikipage to patrol.
    """
    zb.post({'action': 'pagetriageaction',
             'pageid': page.pageid,
             'reviewed': True,
             'skipnotif': True})  # May change based on community's feelings.
    print(f"Patrolled {page.title()}")
    log_local(page, "patrolledpages.txt")
