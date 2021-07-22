"""Functions for interacting with the NewPagesFeed"""
from typing import Literal

import pywikibot as pwb

from utils import ZBError, get, post
from patrol.rfd import checkRfD


def buildqueue(show: list[Literal["showredirs", "showdeleted", "showothers"]],
               start: int = 0) -> list[dict]:
    queue = get({"action": "pagetriagelist",
                 "namespace": "0",
                 "showunreviewed": "1",
                 "dir": "oldestreview",
                 "limit": 200,
                 "date_range_from": start}
                | {i: "1" for i in show})
    try:
        return queue["pagetriagelist"]["pages"]
    except KeyError as e:
        raise ZBError("No pages in queue") from e


def checkqueue():
    queue = buildqueue("showdeleted")
    # Will break when `queue` = [] on reaching the most recent page.
    while queue:
        for page in queue:
            page = pwb.Page(pwb.Site(), title=page["title"])
            if checkRfD(page):
                print(f"Match on {page=}")
                patrol(page)
            else:
                print(f"NO match on {page=}")
        try:
            last = queue[-1]["creation_date"]
        except KeyError as e:
            raise ZBError("No `creation_date` on last entry") from e
        # Intentionally starts next queue on final timestamp, not 1 past
        # it, since timestamps are non-unique.
        queue = buildqueue("showdeleted", start=last)


def patrol(page: pwb.Page):
    post({"action": "pagetriageaction",
          "pageid": page.pageid,
          "reviewed": "1",
          "skipnotif": "1"})  # For now
    raise Exception("You did it! (Once.)")
    # TODO logging
