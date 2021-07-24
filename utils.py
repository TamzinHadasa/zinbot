"""Utility functions for various tasks of 'zinbot."""
from json.decoder import JSONDecodeError
from typing import Callable, Literal

from pywikibot import Page, Site
from requests import Response
from requests_oauthlib import OAuth1Session

from config import bot_token

API_URL = "https://test.wikipedia.org/w/api.php?"
WIKI_URL = "https://test.wikipedia.org/wiki/"


class APIError(Exception):
    """Exception raised by issues in dealing with the MediaWiki API."""

    def __init__(self, msg, event=""):
        super().__init__(msg)
        if event:
            with open("logs/APIError.json", 'w') as f:
                f.write(str(event))


class ZBError(Exception):
    """Generic exception for errors specific to 'zinbot's behavior."""


class Bot:
    """Contains global information for the bot"""
    TokenType = Literal['createaccount', 'csrf', 'deleteglobalaccount',
                        'login', 'patrol', 'rollback',
                        'setglobalaccountstatus', 'userrights', 'watch']

    def __init__(self, token):
        # Signs all API requests with the bot's OAuth data.
        self.session = OAuth1Session(token['c_key'],
                                     client_secret=token['c_secret'],
                                     resource_owner_key=token['a_key'],
                                     resource_owner_secret=token['a_secret'])
        # Yes it caches, but still preferable to only call once
        self.site = Site()

    def _api(self, method: str, **kwargs) -> dict:
        """Error handling and JSON conversion for API functions.

        Args:
          method:  A str matching the name of a method that an
            OAuth1Session can have.
          **kwargs:  Keyword arguments to pass to `method`.

        Returns:
          A dictionary matching the JSON structure of the relevant API
          Response.

        Raises:
          requests.HTTPError:  Issue connecting with API.
          APIError from JSONDecodeError:  API Response output was not
            decodable JSON.
          APIError (native):  API Response included a status > 400 or an
            `error` field in its JSON.
        """
        method: Callable = getattr(self.session, method)
        # Can raise requests.HTTPError
        response: Response = method(API_URL, **kwargs)
        if not response:  # status code > 400
            raise APIError(f"{response.status_code=}", response.content)
        try:
            data: dict = response.json()
        except JSONDecodeError as e:
            raise APIError("No JSON found.", response.content) from e
        if 'error' in data:
            raise APIError("'error' field in response.", response)
        return data

    def get(self, params: dict) -> dict:
        """Send GET request within the OAuth-signed session.

        Automatically specifies output in JSON (overridable).

        Arg:
          params:  Params to supplement/override the default ones.

        Returns / Raises:
          See ._api() documentation.
        """
        return self._api('get',
                         params={"format": "json", **params})

    def post(self, params: dict, tokentype: TokenType = 'csrf') -> dict:
        """Send POST request within the OAuth-signed session.

        Automatically specifies output in JSON (overridable), and sets
        the request's body (a CSRF token) through a get_token() call
        defaulting to CSRF.

        Since Response error handling is internal (through api()), in
        most cases it will not be necessary to access the returned dict.

        Args:
          params:  Params to supplement/override the default ones.
          tokentype:  A TokenType to pass to get_token().  Defaults to
            'csrf' like get_token() and the MW API.

        Returns / Raises:
          See ._api() documentation.
        """
        return self._api('post',
                         params={'format': 'json', **params},
                         data={'token': self.get_token(tokentype)})

    def get_token(self, tokentype: TokenType = 'csrf') -> dict:
        R"""Request a token (CSRF by default) from the MediaWiki API.

        Args:
        tokentype:  A type of token, among the literals defined by
            TokenType.  Defaults to 'csrf' like the MW API.

        Returns:
        A string matching a validly-formatted token of the specified type.

        Raises:
        APIError from KeyError:  If the query response has no token field.
        ZBError:  If the token field is "empty" (just "+\\")
        """
        query = self.get({'action': 'query',
                          'meta': 'tokens',
                          'type': tokentype})
        try:
            # How MW names all tokens.
            token = query['query']['tokens'][tokentype+'token']
        except KeyError as e:
            raise APIError("No token obtained.", query) from e
        if token == R"+\\":
            raise ZBError("Empty token.")
        return token

    def getpage(self, title: str, ns: int = 0,
                must_exist: bool = False) -> Page:
        """Wrapper for pwb.title(), with optional existence check.

        Does not guarantee that page actually exists; check with
        .exists().

        title:  A str matching a valid wikipage title.
        ns:  The MW-defined number for the page's namespace.

        Returns:
          A Page with title `title` in namespace with number `ns`,
          possibly nonexistent (if not `must_exist`).

        Raises:
          ZBError:  If `must_exist` but the page does not exist.
        """
        page = Page(self.site, title=title, ns=ns)
        if must_exist and not page.exists():
            raise ZBError("Page does not exist")
        return page


# All non-PWB API calls through this!  Also PWB Site() requests.
zb = Bot(bot_token)


def log_onwiki(event: str, logpage: str, prefix: str = "User:'zinbot/logs/",
               summary: str = "Updating logs"):
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
    zb.post({'action': 'edit',
             'title': prefix+logpage,
             'appendtext': event,
             'summary': summary})


def log_local(page: Page, logfile: str):
    """Append a page's title and URL to a document in folder `logs/`.

    Args:
      page:  A Page whose title should be logged.
      logfile:  A file (extant or not) in folder `logs/`.
    """
    # NOTE: For now takes full Page as object because there's no reason
    # to duplicate calling .title() within each call.  If used in cases
    # where no Page is involved, `page` could be expanded to take
    # Page|str, only calling .title() in the former case.
    with open(f"logs/{logfile}", 'a') as f:
        f.write(
            page.title()
            + f" <{WIKI_URL}{page.title(as_url=True)}>\n"
        )
