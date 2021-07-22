"""Utility functions for various tasks of 'zinbot"""
from json.decoder import JSONDecodeError
from typing import Callable, Literal

import pywikibot as pwb
import requests
from requests_oauthlib import OAuth1Session

from config import bot


API_URL = "https://test.wikipedia.org/w/api.php?"
# Signs all API requests with the bot's OAuth data
session = OAuth1Session(bot.c_key,
                        client_secret=bot.c_secret,
                        resource_owner_key=bot.a_key,
                        resource_owner_secret=bot.a_secret)
TokenType = Literal['createaccount', 'csrf', 'deleteglobalaccount', 'login',
                    'patrol', 'rollback', 'setglobalaccountstatus',
                    'userrights', 'watch']


class APIError(Exception):
    """Exception raised by issues in dealing with the MediaWiki API"""

    def __init__(self, msg, event=""):
        super().__init__(msg)
        if event:
            with open("logs/APIError.json", 'w') as f:
                f.write(str(event))


class ZBError(Exception):
    """Generic exception for errors specific to 'zinbot's behavior"""


def api(func: Callable, *args, **kwargs):
    """Error handling and JSON conversion for API functions

    Args:
      func:  A `requests` function that interacts with the API.
      *args:  Positional arguments to pass to `func`.
      **kwargs:  Keyword arguments to pass to `func`.

    Returns:
      A dictionary matching the JSON structure of the relevant API
      Response.

    Raises:
      APIError from HTTPError:  Issue connecting with API.
      APIError from JSONDecode:  API Response output was not decodable
        JSON.
      APIError (native):  API Response included a status > 400 or an
        `error` field in its JSON.
    """
    try:
        response: requests.Response = func(*args, **kwargs)
    except requests.HTTPError as e:
        raise APIError from e
    if not response: # status code > 400
        raise APIError(f"{response.status_code=}", response.content)
    try:
        data: dict = response.json()
    except JSONDecodeError as e:
        raise APIError("No JSON found.", response.content) from e
    if 'error' in data:
        raise APIError("'error' field in response.", response)
    return data


def get(params: dict) -> dict:
    """Send GET request within the OAuth-signed session

    Automatically specifies output in JSON.

    Arg:
      params:  Params to supplement/override the default ones.

    Returns / Raises:
      A dict.  See documentation for api().
    """
    return api(session.get,
               API_URL,
               params={"format": "json", **params})


def post(params: dict) -> dict:
    """Send POST request within the OAuth-signed session

    Automatically specifies output in JSON, and sets the request's body
    (a CSRF token) through a get_token() call.

    Since Response error handling is internal (through api()), in most
    cases it will not be necessary to access the returned dict.

    Arg:
      params: Params to supplement/override the default ones.

    Returns / Raises:
      A dict.  See documentation for api().
    """
    return api(session.post,
               API_URL,
               params={'format': 'json', **params},
               data={'token': get_token()})


def get_token(type_: TokenType = "csrf") -> dict:
    R"""Request a token (CSRF by default) from the MediaWiki API

    Args:
      type_:  A type of token, among the literals defined by TokenTypes.
        Defaults to 'csrf', which is also what the API defaults to if
        none is specified.

    Returns:
      A string matching a validly-formatted token of the specified type.

    Raises:
      APIError from KeyError:  If the query response has no token field.
      ZBError:  If the token field is "empty" (just "+\\")
    """
    query = get({'action': 'query',
                 'meta': 'tokens',
                 'type': type_})
    try:
        token = query['query']['tokens'][type_+'token']
    except KeyError as e:
        raise APIError("No token obtained.", query) from e
    if token == R"+\\":
        raise ZBError("Empty token.")
    return token


def log_onwiki(event: str, title: str, prefix: str = "User:'zinbot/logs/",
               summary: str = "Updating logs"):
    """Log an event to a page on-wiki.

    Defaults to a subpage of `User:'zinbot/logs/`.

    Args:
      event:  A string, to be appended to the page in question.
      title:  A string, which when appended to `prefix` forms a page's
        full title on-wiki.
      prefix:  A string to go before `title`.  To be specified if the
        log will not be in the normal place.
      summary:  A custom edit summary to use.
    """
    post({'action': 'edit',
          'title': prefix+title,
          'appendtext': event,
          'summary': summary})


def log_local(page: pwb.Page, logfile: str):
    """Append a page's title and URL to a document in folder logs/"""
    with open(f"logs/{logfile}", 'a') as f:
        f.write(
            page.title()
            + f" <https://test.wikipedia.org/wiki/{page.title(as_url=True)}>\n"
        )
