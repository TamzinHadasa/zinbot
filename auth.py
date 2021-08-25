"""Authorization class, to be called privately from `config`."""
from dataclasses import dataclass

from requests_oauthlib import OAuth1Session


@dataclass
class Authorization:
    """Dataclass for OAuth1Token.  Call privately in config.

    Args / Attributes:
      Match the output of the MW OAuth consumer dialog.
    """
    client_key: str
    client_secret: str
    access_key: str
    access_secret: str

    def __repr__(self) -> str:
        return (f"Authorization({self.client_key}, {self.client_secret}, "
                f"{self.access_key}, {self.access_secret})")

    def __str__(self) -> str:
        return f"<Authorization object with access key {self.access_key}>"

    def session(self) -> OAuth1Session:
        """Create OAuth1Session using instance data attributes."""
        return OAuth1Session(self.client_key,
                             client_secret=self.client_secret,
                             resource_owner_key=self.access_key,
                             resource_owner_secret=self.access_secret)
