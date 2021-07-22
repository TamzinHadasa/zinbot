"""Functions for detecting and patrolling RfD'd pages

When a redirect is nominated for discussion at RfD, it is placed in the
articles queue of Special:NewPagesFeed.  These functions identify such
"articles", double-check that they've been filed to RfD, and, if so,
patrol them.  After 30 minutes of not being filed to RfD, a page is
logged as such on-wiki.
"""
import datetime as dt
import logging

import mwparserfromhell as parser
import pywikibot as pwb

from utils import log


def checkRfD(page: pwb.Page) -> bool:
    INVOCATION = "<includeonly>safesubst:</includeonly>#invoke:RfD"
    parsed = parser.parse(page.text)
    if INVOCATION not in parsed:
        return False
    # ugly hack around https://github.com/earwig/mwparserfromhell/issues/251
    parsed.replace(INVOCATION, "fake template")
    template = parsed.filter_templates()[0]
    year, month, day = (template.get(s).value.strip()
                        for s in ("year", "month", "day"))
    rfd = pwb.Page(
        pwb.Site(),
        title=f"Redirects for discussion/Log/{year} {month} {day}",
        ns=4  # Project:
    )
    filed = f'*<span id="{page.title()}">' in rfd.text
    if not filed:
        handle_unfiled(page, rfd)
    return filed


def handle_unfiled(page: pwb.Page, rfd: pwb.Page):
    logging.info(f"NOT FILED: {page.title()} @{dt.datetime.now()}\n")
    edited: pwb.Timestamp = page.editTime()  # Subclass of dt.datetime
    now = pwb.Site().server_time()
    if now - edited > dt.timedelta(minutes=30):
        log(event=(f"* {page.title(as_link=True)} not filed to "
                   f"{rfd.title(as_link=True)} as of {now}\n"),
            title="Unfiled RfDs")
