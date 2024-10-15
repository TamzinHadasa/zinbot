"""Interacting with the NewPagesFeed."""
import client
from classes import ZBError
from pagetriage import rfd


class QueueError(ZBError):
    """Error raised in interacting with the queue."""


def checkqueue() -> None:
    """Loop through NewPagesFeed, 200 items at a time.

    Uses `_buildqueue`, set to 'showdeleted' mode.

    Raises:
      QueueError if an entry does not have a creation date.
    """
    unreviewed_titles = []
    queue = client.buildqueue(showdeleted="y")
    # The practical limit on this is that, if there's some unforeseen
    # situation that can cause an infinite loop, the resulting HTTP 429
    # response would halt the bot as provided for in `api._request`.
    while True:
        unreviewed_titles += [i['title'] for i in queue]
        for page_data in queue:
            page_title = page_data['title']
            page = client.get_page(page_title)
            if rfd.check_rfd(page):
                print(f"***MATCH*** on {page_title=}")
                client.review(page)
                unreviewed_titles.remove(page_title)
            else:
                print(f"No criteria met on {page_title=}")
        try:
            last: int = queue[-1]['creation_date']
        except KeyError as e:  # Unlikely to ever happen but...
            raise QueueError("No 'creation_date' on last entry") from e
        # Intentionally starts next queue on final timestamp, not 1 past
        # it, since timestamps are non-unique.  Repeating is harmless,
        # as long as we account for the fact that `newqueue` will thus
        # always have a length of at least 1.
        newqueue = client.buildqueue(showdeleted="y", start=last)
        # In theory would also cause a break if 200+ entries have the
        # same timestamp.  Yeah, that's fine.
        if not newqueue or queue[-1]['pageid'] == newqueue[-1]['pageid']:
            break
        queue = newqueue
    print("Queue complete. Checking if log cleanup is necessary.")
    rfd.cleanup(unreviewed_titles)
