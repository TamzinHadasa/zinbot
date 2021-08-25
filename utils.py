"""Utility functions."""
from pywikibot import Page

import api

_WIKI_URL = "https://test.wikipedia.org/wiki/"


class ZBError(Exception):
    """Generic exception for errors specific to 'zinbot's behavior."""


def log_onwiki(event: str,
               logpage: str,
               prefix: str = "User:'zinbot/logs/",
               summary: str = "Updating logs") -> None:
    """Log an event to a page on-wiki.

    Defaults to a subpage of `User:'zinbot/logs/`.

    Args:
      event:  A string, to be appended to the page in question.
      logpage:  A string, which when appended to `prefix` forms a page's
        full title on-wiki.
      prefix:  A string to go before `title`.  To be specified if the
        log will not be in the normal place.
      summary:  A custom edit summary to use.
    """
    api.post({'action': 'edit',
              'title': prefix + logpage,
              'appendtext': event,
              'summary': summary})


# NOTE: For now takes full Page as object because there's no reason to
# duplicate calling .title() within each call.  If used in cases where
# no Page is involved, `page` could be expanded to take Page|str, only
# calling .title() in the former case.
def log_local(page: Page, logfile: str) -> None:
    """Append a page's title and URL to a document in folder `logs/`.

    Args:
      page:  A Page whose title should be logged.
      logfile:  A file (extant or not) in folder `logs/`.
    """
    with open(f"logs/{logfile}", 'a') as f:
        f.write(
            page.title()
            + f" <{_WIKI_URL}{page.title(as_url=True)}>\n"
        )
