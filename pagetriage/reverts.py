"""Patrolling pages that were self-reverts or vandalism reverts."""
import datetime as dt
import re

from mwclient.page import Page  # type:ignore[import-untyped]

from classes import Group, Revision, User


_RV_SUMMARIES = re.compile(r"((mass ?)?(und(o|id)|revert|rvv?|rb)|restore)\b")


def _get_revs(page: Page, start: int = 0, end: int = 0):
    """Get a previous revision of a page, `back` revisions ago.
    
    Args:
      back:  An int of a number of revisions.  0 means current.
    """
    revs_raw = list(page.revisions(
        rvlimit=end,
        prop='content|comment|timestamp|flags|user'
    ))
    return [Revision(r) for r in revs_raw[start:end+1]]


def _check_eligibility(page: Page) -> bool:
    cur, prev, ere_prev = _get_revs(page, 0, 2)
    return all([
        _check_if_timely(cur, prev),
        (_check_if_rollback(cur, prev, ere_prev)
         or _check_if_self_rv(cur, prev))
    ])


def _check_if_timely(new: Revision, old: Revision) -> bool:
    return new.timestamp - old.timestamp <= dt.timedelta(days=1)


def _check_if_rollback(
        newest: Revision, prev: Revision, ere_prev: Revision
    ) -> bool:
    return all([
        newest.minor,
        _RV_SUMMARIES.match(newest.comment.lower()),
        _check_perms(newest.user_info(), {Group.PATROLLER, Group.REVIEWER,
                                          Group.ROLLBACKER, Group.SYSOP}),
        not _check_perms(prev.user_info(), {Group.XCON}),
        newest.text == ere_prev.text
    ])


def _check_perms(user: User, groups: set[Group]) -> bool:
    return bool(user.groups & groups)


def _check_if_self_rv(
        newest: Revision, prev: Revision, ere_prev: Revision
    ) -> bool:
    return all(
        newest.username == prev.username
    )