from dotenv import load_dotenv
import os
import anaplan_sdk
from fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("plan-agent")


def _refresh_auth() -> anaplan_sdk.AnaplanRefreshTokenAuth:
    """Complete OAuth2 authentication
    returns subclass of httpx.Auth including automatic refresh mechanism
    """
    client_id=os.environ["ANAPLAN_CLIENT_ID"]
    client_secret=os.environ["ANAPLAN_CLIENT_SECRET"]
    redirect_uri=os.environ["ANAPLAN_REDIRECT_URI"]
    state=os.environ["STATE"]
    authorization_response=os.environ["AUTHORIZATION_RESPONSE"]
    anaplan_auth:anaplan_sdk._oauth.Oauth = anaplan_sdk.Oauth(
        client_id,
        client_secret,
        redirect_uri
    )
    token:dict[str, str | int] = anaplan_auth.fetch_token(
        authorization_response,
        state
    )
    refresh_auth = anaplan_sdk.AnaplanRefreshTokenAuth(
        client_id, client_secret, redirect_uri, token
    )
    return refresh_auth

CLIENT = anaplan_sdk.Client (
    auth=_refresh_auth (),
    workspace_id=os.environ["WORKSPACE_ID"],
    model_id=os.environ["MODEL_ID"]
)


@mcp.resource("anaplan://me")
def me() -> dict:
    """Return the currently authenticated Anaplan user."""
    return CLIENT.audit.get_user().model_dump()


@mcp.tool()
def wake_data_hub(workspace_id: str, model_id: str, action_id: int) -> dict:
    """Run an Anaplan action to wake the data hub for the specified model."""
    result = CLIENT.run_action(action_id)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
