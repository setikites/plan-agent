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

"""

from dotenv import load_dotenv, set_key
import os
from pathlib import Path
import webbrowser

import anaplan_sdk

env_path = Path (".env")
load_dotenv()
CLIENT_ID = os.environ["ANAPLAN_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANAPLAN_CLIENT_SECRET"]
REDIRECT_URI = os.environ['ANAPLAN_REDIRECT_URI']

anaplan_auth:anaplan_sdk._oauth.Oauth = anaplan_sdk.Oauth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


def login():
    """Generate an authorization URL and open a browser tab with that
    to initiate the OAuth2 login sequence.

    Returns state string
    This state string can be passed to redirect for additional security.
    """
    authorization_url, state = anaplan_auth.authorization_url()
    webbrowser.open(authorization_url)
    authorization = input ("Paste the enitre redirect UFL here: ")
    set_key (env_path, "STATE", state)
    set_key (env_path, "AUTHORIZATION_RESPONSE", authorization)



if __name__ == "__main__":
    login ()
