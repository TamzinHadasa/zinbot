"""Detecting and patrolling RfD'd pages.

When a redirect is nominated for discussion at RfD, it is placed in the
articles queue of Special:NewPagesFeed.  This module identifies such
"articles", double-checks that they've been filed to RfD, and, if so,
patrols them, otherwise logging the error on-wiki.
"""
from enum import Enum
from typing import Literal, Optional

from mwclient.page import Page  # type:ignore[import-untyped]
import mwparserfromhell as mwph  # type:ignore[import-untyped]
from mwparserfromhell.nodes import Heading, Tag  # type:ignore[import-untyped]

import client
from client import PageNotFoundError
from classes import Namespace, SensitiveList, Title
from logging_ import OnWikiLogger


_onwiki_logger = OnWikiLogger("skippedRfDs.json")


class _Messages(Enum):
    RFD0 = "[[{page}]] not filed to [[{rfd}]] (currently a redlink)."
    RFD1 = "[[{page}]] not filed to [[{rfd}]]."
    RFD2 = ("[[{page}]] filed to [[{rfd}]], but that log page has "
            "not been transcluded to main RfD page.")
    # RFD3 removed

def _get_rfd_date_params_if_any(page: Page) -> Optional[dict[Literal['year', 'month', 'day'], str]]:
    """Return date params from RfD tag, if either has been called.

    Uses the standard RfD log format and the `year`, `month`, and `day`
    parameters in {{subst:rfd}}.  This accounts for RfDs filed to
    previous dates.

    Arg:
      page:  A Page.

    Returns:
      A tuple of strs, or None.
    """
    # Ugly hack around <https://github.com/earwig/mwparserfromhell/issues/251>.
    text = page.text().replace("<includeonly>safesubst:</includeonly>", "")
    parsed = mwph.parse(text)
    for template in parsed.filter_templates():
        if template in ("#invoke:RfD", "Rfd-NPF/core"):
            return {s: template.get(s).value.strip()  # type: ignore[misc]
                    for s in ("year", "month", "day")}
    return None


def _check_filed(page: Page, year: str, month: str, day: str) -> bool:
    """Check an RfD log page for an anchor matching the page's title.

    {{subst:rfd2}} makes such anchors automatically.  As with TAGGED, no
    guarantee of matching markup that renders the same way but is
    generated through some other means.

    Arg:
      page:  A Page corresponding to a wikipage tagged with
        {{subst:rfd}}.

    Returns:
      A bool indicating whether an RfD entry exists matching the page's
      title.
    """
    rfd_title = Title(Namespace.PROJECT,
                      f"Redirects for discussion/Log/{year} {month} {day}")
    page_title = Title.from_page(page)
    try:
        rfd = client.get_page(title=rfd_title.pagename,
                              ns=rfd_title.namespace,
                              must_exist=True)
    except PageNotFoundError:
        print(f"No RfD page for {page_title}.")
        _onwiki_logger.log(_Messages.RFD0, page_title, rfd=rfd_title)
        return False

    # What idiot made this line necessary by building quotation-mark escaping
    # into {{rfd2}}?  Oh right.  Me.
    anchor = page_title.replace('"', "&quot;").removeprefix(":")
    parsed = mwph.parse(rfd.text())
    filed: list[Tag] | list[Heading] = (
        parsed.filter_headings(
            matches=lambda heading: _compress_ws(heading.title) == anchor
        )
        or parsed.filter_tags(
            matches=lambda tag: _is_correct_anchor(tag, anchor)
        )
    )
    transcluders = [i.name for i in rfd.embeddedin()]

    if not filed:
        print(f"RfD not filed for {page_title}.")
        _onwiki_logger.log(_Messages.RFD1, page_title, rfd=rfd_title)
    elif "Wikipedia:Redirects for discussion" not in transcluders:
        print(f"{rfd_title} not transcluded to main RfD page.")
        _onwiki_logger.log(_Messages.RFD2, page_title, rfd=rfd_title)
        return False
    return True


def _is_correct_anchor(tag: Tag, target: str) -> bool:
    if tag.tag != 'span':
        return False
    try:
        # `strip('"')` could obscure HTML errors
        id_ = (tag.get('id').split("=", maxsplit=1)[1]
               .removeprefix('"').removesuffix('"'))
    except ValueError:  # If span has no id.
        return False
    return _compress_ws(id_) == target


def _compress_ws(text: str) -> str:
    return " ".join(text.split())


def check_rfd(page: Page) -> bool:
    """Check if a page is subject to an ongoing RfD.

    First checks for the {{subst:rfd}} tag, then for whether there's an
    entry at the corresponding RfD log page.

    Arg:
      page:  A Page corresponding to a wikipage to be checked.

    Returns:
      A bool, True if both TAGGED matches and checkfiled() returns True.
      (If the former but not the latter, the distinction is made clear
      by logs.)
    """
    date_params = _get_rfd_date_params_if_any(page)
    if date_params is None:
        return False
    return _check_filed(page, **date_params)  # type: ignore[misc]  # https://github.com/python/mypy/issues/10023


def cleanup(unreviewed_titles: list[str]) -> None:
    """Remove old and resolved log entries.

    Returns:
      A bool indicating whether cleanup occurred.
    """
    with _onwiki_logger.edit("Removing old and/or reviewed entries.") as data:
        for day, entries in data.copy().items():
            if _onwiki_logger.day_too_old(day):
                del data[day]
            else:
                entries = SensitiveList(
                    [i for i in entries
                     if i['page'].removeprefix(":") in unreviewed_titles]
                )
                if not entries:
                    del data[day]
                else:
                    data[day] = entries
        if data.been_changed():
            print("Cleaning up skippedRfDs.json")
