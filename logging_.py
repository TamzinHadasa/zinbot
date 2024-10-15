"""Logging features."""
from contextlib import contextmanager
import datetime as dt
from enum import Enum
import json
from typing import Any, Generator

import client
import constants
from classes import Event, Namespace, SensitiveDict, SensitiveList, Title

LoggerData = SensitiveDict[str, SensitiveList[Event]]


class OnWikiLogger:
    """Controls on-wiki logging of events."""
    _dateformat = "%Y-%m-%d"
    _timestampformat = "%Y-%m-%d %H:%M:%S (UTC)"

    def __init__(
        self,
        logpage: str,
        ns_and_basepage: tuple[Namespace, str] = (Namespace.USER,
                                                  "'zinbot/logs/")
    ) -> None:
        """Initialize an OnWikiLogger.

        Args:
          logpage:  A str of a subpage name.
          ns_and_basepage:  A tuple of a Namespace and a str of a basepage
            name.
        """
        self._logpage = logpage
        self._ns_and_basepage = ns_and_basepage
        self._logtitle = Title(ns_and_basepage[0],
                               ns_and_basepage[1] + logpage)

    def __repr__(self) -> str:
        return f"Logger({self._logpage}, {self._ns_and_basepage})"

    @classmethod
    def day_too_old(cls, timestamp: str) -> bool:
        """See if a log entry is more than 7 days old.

        Arg:
          timestamp:  A str drawn from an Event's 'timestamp' item.

        Returns:
          A bool indicating whether the timestamp is more than 7 days
            ago.
        """
        as_date = dt.datetime.strptime(timestamp, cls._dateformat).date()
        return dt.datetime.now().date() - as_date > dt.timedelta(days=7)

    def _load_json(self) -> LoggerData:
        text = client.get_page(self._logtitle.pagename,
                               self._logtitle.namespace).text() or "{}"
        return SensitiveDict({k: SensitiveList(v)
                              for k, v in json.loads(text).items()})

    def _save_json(self, data: LoggerData, summary: str) -> None:
        page = client.get_page(self._logtitle.pagename,
                               self._logtitle.namespace)
        page.edit(text=json.dumps(data), summary=summary)

    @contextmanager
    def edit(self, summary: str) -> Generator[LoggerData, None, None]:
        """Context manager for editing the log.

        Arg:
          summary:  A str to use as the edit summary when saving.

        Yields:
          A generator of LoggerData.
        """
        data = self._load_json()
        try:
            yield data
        finally:
            if data.been_changed():
                self._save_json(data, summary)

    def log(self,
            message: Enum,
            page: str,
            **formatters: Any) -> None:
        """Log an event.

        Arg:
          message:  An Enum, the name of which can serve as an error
            code and the value of which is an error message.
          page:  A str of a page's title, including leading colon for
            mainspace.
          **formatters:  Objects to pass to the Enum's value for
            formatting.
        """
        with self.edit(f"Logging [[{page}]] (code {message.name})") as data:
            if page in [i['page'] for day in data.values() for i in day]:
                return  # Skip if already logged.
            now = dt.datetime.now()  # Avoid midnight race condition.
            today = now.strftime(self._dateformat)
            if today not in data:
                data[today] = SensitiveList([])
            data[today].append({
                'page': page,
                'code': message.name,
                'message': message.value.format(page=page, **formatters),
                'timestamp': now.strftime(self._timestampformat)
            })
