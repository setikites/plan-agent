"""Authentication using OAuth2 for fastmcp

Read envirinment variables from .env
Generate the authorizaiton URL and state
Open the authorizaiton URL
Input the authorization response
Write .env with:
- client id
- client secret
- redirect URL
- state
- authorization response

The fastmcp server will import those environment variables and use
them to fetch the authorization token.

NOTES:
above did not work.
Now try completing login in this script and saving the entire JSON token with refresh to a file.
Then load that file to create a stdio MCP server.
token = anaplan._http._client.auth.token


"""

from dotenv import load_dotenv
import json
import os
from pathlib import Path

import anaplan_sdk

TOKEN_PATH = Path(".token.json")
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
    json_data = json.dumps(token, indent=2)
    with open(TOKEN_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(json_data)


if __name__ == "__main__":
    login()
