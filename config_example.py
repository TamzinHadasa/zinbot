from auth import Authorization

# You can create multiple Authorization objects for different users.  To
# switch them out, just change `DEFAULT_USER` below.
# Strictly speaking the keys here don't have to be usernames, but it's
# easier to remember if they are.
_users = {"username1": Authorization(client_key="",
                                     client_secret="",
                                     access_key="",
                                     access_secret="")
DEFAULT_USER = _users["username1"]
# A MediaWiki site's name.  Everything between "https://" and the first slash
# or question mark
DEFAULT_SITE = 'en.wikipedia.org'
