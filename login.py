"""Authentication using OAuth2 for fastmcp

This script completes authentication and saves the encrypted token to
a file.  The main.py script reads the encrypted token to authenticate
the MCP server.

"""

import json
import keyring
import os

import anaplan_sdk
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.environ["ANAPLAN_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANAPLAN_CLIENT_SECRET"]
REDIRECT_URI = os.environ["ANAPLAN_REDIRECT_URI"]
SPLIT = 1240                    # MS Windows len(password) < 1280


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
    part_a = json_data[:SPLIT]
    part_b = json_data[SPLIT:]
    keyring.set_password("Anaplan_a", os.getlogin (), part_a)
    keyring.set_password("Anaplan_b", os.getlogin (), part_b)


if __name__ == "__main__":
    login()
