"""Functions for interacting with the NewPagesFeed"""
from typing import Literal

import pywikibot as pwb

from utils import ZBError, get, post, log_local
from patrol.rfd import checkRfD


# Setting `start` to 0 throws an error with the API.
def buildqueue(show: list[Literal['showredirs', 'showdeleted', 'showothers']],
               start: int = 1) -> list[dict]:
    """Build a NewPagesFeed queue of unreviewed pages in the mainspace.

    Args:
      show:  A list containing any of the following: 'showredirs',
        'showdeleted', and 'showothers'.  These will be set to boolean 1
        in the queue's parameters.  (N.B.:  'showdeleted' means
        "nominated for deletion", not "deleted".)  Setting none of these
        is the same as setting all of them.
      start:  A timestamp to start at, in standard MediaWiki format
        (YYYYMMDDHHMMSS).

    Returns:
      A list of dicts, potentially empty, based on on the 'pages' field
      of the JSON returned by the API.
    """
    queue = get({'action': 'pagetriagelist',
                 'namespace': 0,  # Main
                 'showunreviewed': 1,
                 'dir': 'oldestreview',
                 'limit': 200,  # NOTE move to constant if reference elsewhere
                 'date_range_from': start}
                | {i: 1 for i in show})
    return queue['pagetriagelist']['pages']


def checkqueue():
    """Loop through NewPagesFeed, 200 items at a time

    Uses buildqueue(), set to 'showdeleted' mode.
    """
    queue = buildqueue(['showdeleted'])
    # TODO failsafe against infinite loop to avoid API lockout
    while True:
        for page in queue:
            page = pwb.Page(pwb.Site(), title=page['title'])
            if checkRfD(page):
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


def patrol(page: pwb.Page):
    """Patrol a page using PageTriage.

    Arg:
      page:  A pwb.Page representing a wikipage to patrol.
    """
    # post({'action': 'pagetriageaction',
    #       'pageid': page.pageid,
    #       'reviewed': 1,
    #       'skipnotif': 1})  # For now
    log_local(page, "patrolledpages.txt")
