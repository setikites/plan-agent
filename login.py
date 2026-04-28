"""Authentication using OAuth2 for fastmcp

This script completes authentication and saves the encrypted token to
a file.  The main.py script reads the encrypted token to authenticate
the MCP server.

"""

from dotenv import load_dotenv
import json
import os
from pathlib import Path

import anaplan_sdk
import crypto

FILENAME = Path (".token")
load_dotenv()
CLIENT_ID = os.environ["ANAPLAN_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANAPLAN_CLIENT_SECRET"]
REDIRECT_URI = os.environ["ANAPLAN_REDIRECT_URI"]


def login():
    """Generate an authorization URL and open a browser tab with that
    to initiate the OAuth2 login sequence.

    Returns state string
    This state string can be passed to redirect for additional security.
    """
    refresh_auth = anaplan_sdk.AnaplanLocalOAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI
    )
    token = refresh_auth._oauth_token
    json_data = json.dumps(token)
    my_key = crypto.load_key()
    crypto.encrypt_and_write (FILENAME, json_data, my_key)


if __name__ == "__main__":
    crypto.generate_key()
    login()
