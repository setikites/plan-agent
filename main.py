from dotenv import load_dotenv
import json
import os
from pathlib import Path

import anaplan_sdk
from fastmcp import FastMCP

TOKEN_PATH = Path(".token.json")
load_dotenv()
mcp = FastMCP("plan-agent")


def _refresh_auth() -> anaplan_sdk.AnaplanRefreshTokenAuth:
    """Complete OAuth2 authentication
    returns subclass of httpx.Auth including automatic refresh mechanism
    """
    client_id = os.environ["ANAPLAN_CLIENT_ID"]
    client_secret = os.environ["ANAPLAN_CLIENT_SECRET"]
    redirect_uri = os.environ["ANAPLAN_REDIRECT_URI"]
    with open(TOKEN_PATH, "r", encoding="utf-8", newline="") as f:
        json_str = f.read()
        token: dict[str, str | int] = json.loads(json_str)
    refresh_auth = anaplan_sdk.AnaplanRefreshTokenAuth(
        client_id, client_secret, redirect_uri, token
    )
    return refresh_auth


@mcp.resource("anaplan://me")
def me() -> dict:
    """Return the currently authenticated Anaplan user."""
    client = anaplan_sdk.Client(
        auth=_refresh_auth(),
        workspace_id=os.environ["WORKSPACE_ID"],
        model_id=os.environ["MODEL_ID"],
    )
    return client.audit.get_user().model_dump()


@mcp.resource("anaplan://workspace/{workspace_id}/models/{model_id}/processes")
def get_processes(
        workspace_id: str=os.environ["WORKSPACE_ID"],
        model_id: str=os.environ["MODEL_ID"]
) -> str:
    """Return all processes in an Anaplan model.

    The Anaplan model is within an Anaplan workspace.
    """
    client = anaplan_sdk.Client(
        auth=_refresh_auth(),
        workspace_id=workspace_id,
        model_id=model_id
    )
    return json.dumps([proc.model_dump() for proc in client.get_processes()])

@mcp.resource("anaplan://workspaces{?search_pattern}")
def get_workspaces (
        search_pattern: str | None = None
) -> str:
    """Return all Anaplan workspaces.

        :param search_pattern:  **Caution: This is an undocumented Feature and may behave
               unpredictably. It requires the Tenant Admin role. For non-admin users, it is
               ignored.** Optionally filter for specific workspaces. When provided,
               case-insensitive matches workspaces with names containing this string.
               You can use the wildcards `%` for 0-n characters, and `_` for exactly 1 character.
               When None (default), returns all users.
    """
    client = anaplan_sdk.Client(
        auth=_refresh_auth()
    )
    return json.dumps([ws.model_dump() for ws in client.get_workspaces(
        search_pattern=search_pattern
    )])

@mcp.resource("anaplan://workspaces/{workspace_id}/models{?only_in_workspace,search_pattern}")
def get_models (
        workspace_id: str=os.environ["WORKSPACE_ID"],
        only_in_workspace: bool = False,
        search_pattern: str | None = None
) -> str:
    """Return all Anaplan models.

        :param only_in_workspace: If True, only lists models in the workspace provided when
               instantiating the client. If a string is provided, only lists models in the workspace
               with the given Id. If False (default), lists models in all workspaces the user
        :param search_pattern:  **Caution: This is an undocumented Feature and may behave
               unpredictably. It requires the Tenant Admin role. For non-admin users, it is
               ignored.** Optionally filter for specific models. When provided,
               case-insensitive matches model names containing this string.
               You can use the wildcards `%` for 0-n characters, and `_` for exactly 1 character.
               When None (default), returns all models.
    """
    client = anaplan_sdk.Client(
        auth=_refresh_auth(),
        workspace_id=workspace_id
    )
    return json.dumps([model.model_dump() for model in client.get_models(
        only_in_workspace=only_in_workspace,
        search_pattern=search_pattern
    )])


@mcp.tool()
def run_action(
        action_id: int,
        workspace_id: str=os.environ["WORKSPACE_ID"],
        model_id: str=os.environ["MODEL_ID"]
) -> dict:
    """Run an Anaplan action.

    Actions can be imports, exports, processes or other actions like
    delete, optimize, or sort.

    This tool is not recommended for file
    imports or exports or processes that include file imports or
    exports.

    """
    client = anaplan_sdk.Client(
        auth=_refresh_auth(),
        workspace_id=workspace_id,
        model_id=model_id
    )
    result = client.run_action(action_id)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
