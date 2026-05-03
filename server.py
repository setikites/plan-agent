import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import anaplan_sdk
from dotenv import load_dotenv
from fastmcp import Context, FastMCP

import crypto

TOKEN_PATH = Path(".token.json")
FILENAME = Path(".token")
load_dotenv()


def _build_auth() -> anaplan_sdk.AnaplanRefreshTokenAuth:
    """Build an OAuth2 auth object with automatic token refresh.

    Reads credentials from environment variables and decrypts the stored
    token file. Called once at server startup via lifespan.
    """
    client_id = os.environ["ANAPLAN_CLIENT_ID"]
    client_secret = os.environ["ANAPLAN_CLIENT_SECRET"]
    redirect_uri = os.environ["ANAPLAN_REDIRECT_URI"]
    my_key = crypto.load_key()
    json_str = crypto.read_and_decrypt(FILENAME, my_key)
    token = json.loads(json_str)
    return anaplan_sdk.AnaplanRefreshTokenAuth(
        client_id, client_secret, redirect_uri, token
    )


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Build auth once at startup and share it across all tools and resources.

    AnaplanRefreshTokenAuth handles token refresh automatically, so the single
    auth instance stays valid for the lifetime of the server process.
    """
    auth = _build_auth()
    yield {"auth": auth}


mcp = FastMCP(
    "plan-agent",
    lifespan=lifespan,
    instructions="""Interact with objects in an Anaplan cloud tenant
    to support planning, forecasting, and budgeting activity.

    Here are how the objects relate to one another:
    - Workspaces contain models.
    - Models contain dimensions like time, versions, and other lists.
    - Models also contain modules with line items that have cells at
      every intersection of their dimensions.
    - Modules contain line items and cells.
    - Cells for line items with formulas store the result of the formula.
    - Cells for line items without formulas store data.
    - Line items have formats, like number, text, date, list item, boolean,
      or period.
    - Lists contain list items.
    - List items have a name and may have a parent or a code.
    - One list may be the parent of another list, forming a hierarchy.
    - Time in a model is represented by the model calendar and time ranges.
    - Actions are used for bulk interaction with a model.
    - Actions include import, export, delete, sort, and can be combined in
      sequential processes.
    - Users interact with apps to view or update data in models.
    - Apps have pages.
    - Each page contains cards from a single model.
    - Cards display data from modules or views.
    - Modules have views that organize dimensions into pages, rows, and columns.
    - Module views may also show only part of the data in a module.
    - Import actions load data from saved views or files into a list or module.
    - Export actions load data from moduiles or lists into a file.
    - Files can be uploaded to a model or downloaded from a model.
    """
)


@mcp.resource(
    uri="anaplan://me",
    tags={"user", "integration", "transactional"}
)
def me(ctx: Context) -> dict:
    """Return the currently authenticated Anaplan user."""
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"],
        workspace_id=os.environ["WORKSPACE_ID"],
        model_id=os.environ["MODEL_ID"],
    )
    return client.audit.get_user().model_dump()


@mcp.resource(
    uri="anaplan://processes{?workspace_id,model_id}",
    tags={"action", "process", "integration", "bulk"}
)
def get_processes(
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> str:
    """Return all processes in an Anaplan model.

    The Anaplan model is within an Anaplan workspace.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    return json.dumps([proc.model_dump() for proc in client.get_processes()])


@mcp.resource(
    uri="anaplan://imports{?workspace_id,model_id}",
    tags={"action", "import", "integration", "bulk"}
)
def get_imports(
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> str:
    """Return all imports in an Anaplan model.

    The Anaplan model is within an Anaplan workspace.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    return json.dumps([proc.model_dump() for proc in client.get_imports()])


@mcp.resource(
    uri="anaplan://exports{?workspace_id,model_id}",
    tags={"action", "import", "integration", "bulk"}
)
def get_exports(
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> str:
    """Return all exports in an Anaplan model.

    The Anaplan model is within an Anaplan workspace.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    return json.dumps([proc.model_dump() for proc in client.get_exports()])


@mcp.resource(
    uri="anaplan://workspaces{?search_pattern}",
    tags={"workspace", "integration", "transactional"}
)
def get_workspaces(ctx: Context, search_pattern: str | None = None) -> str:
    """Return all Anaplan workspaces.

    :param search_pattern:  **Caution: This is an undocumented Feature and may behave
           unpredictably. It requires the Tenant Admin role. For non-admin users, it is
           ignored.** Optionally filter for specific workspaces. When provided,
           case-insensitive matches workspaces with names containing this string.
           You can use the wildcards `%` for 0-n characters, and `_` for exactly 1 character.
           When None (default), returns all users.
    """
    client = anaplan_sdk.Client(auth=ctx.lifespan_context["auth"])
    return json.dumps(
        [ws.model_dump() for ws in client.get_workspaces(search_pattern=search_pattern)]
    )


@mcp.resource(
    uri="anaplan://workspaces/{workspace_id}/models{?only_in_workspace,search_pattern}",
    tags={"model", "integration", "transactional"}
)
def get_models(
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    only_in_workspace: bool = False,
    search_pattern: str | None = None,
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
    client = anaplan_sdk.Client(auth=ctx.lifespan_context["auth"], workspace_id=workspace_id)
    return json.dumps(
        [
            model.model_dump()
            for model in client.get_models(
                only_in_workspace=only_in_workspace, search_pattern=search_pattern
            )
        ]
    )


@mcp.resource(
    uri="anaplan://models/{model_id}/modules",
    tags={"module", "integration", "transactional"}
)
def get_modules(
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> str:
    """Return all modules in one Anaplan model."""
    client = anaplan_sdk.Client(auth=ctx.lifespan_context["auth"], workspace_id=workspace_id)
    return json.dumps([model.model_dump() for model in client.tr.get_modules()])


@mcp.resource(
    uri="anaplan://models/{model_id}/views",
    tags={"view", "integration", "transactional"}
)
def get_views(
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> str:
    """Return all views in one Anaplan model."""
    client = anaplan_sdk.Client(auth=ctx.lifespan_context["auth"], workspace_id=workspace_id)
    return json.dumps([model.model_dump() for model in client.tr.get_views()])


@mcp.tool(
    tags={"action", "integration", "bulk"}
)
def run_action(
    action_id: int,
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> dict:
    """Run an Anaplan action.

    Actions can be imports, exports, processes or other actions like
    delete, optimize, or sort.

    This tool is not recommended for file
    imports or exports or processes that include file imports or
    exports.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    result = client.run_action(action_id)
    return result.model_dump()


@mcp.tool(
    tags={"action", "export", "integration", "bulk"}
)
def export_and_download(
    export_id: int,
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> bytes:
    """Run an Anaplan export action and download the resulting file.

    This tool is not recommended for process actions because it expects that the export_id and the file_id are the same.  While this is true for export actions, it is not true for processes.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    result = client.export_and_download(export_id)
    return result


@mcp.tool(
    tags={"action", "import", "integration", "bulk"}
)
def upload_and_import(
    file_id: int,
    content: str | bytes,
    import_id: int,
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> dict:
    """Run an Anaplan import action and download the resulting file.

    This tool is not recommended for process actions because it expects that the import_id and the file_id are the same.  While this is true for import actions, it is not true for processes.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    result = client.upload_and_import(
        file_id=file_id, content=content, action_id=import_id
    )
    return result.model_dump()


@mcp.tool(
    tags={"update", "integration", "transactional"}
)
def update_module_data(
    module_id: int,
    data: list[dict[str, Any]],
    ctx: Context,
    workspace_id: str = os.environ["WORKSPACE_ID"],
    model_id: str = os.environ["MODEL_ID"],
) -> str:
    """Write the passed items to the specified module. If successful,
    the number of cells changed is returned, if only partially
    successful or unsuccessful, the response with the according
    details is returned instead.

    **You can update a maximum of 100,000 cells or 15 MB of data
    (whichever is lower) in a single request.** You must chunk
    your data accordingly. This is not done by this SDK, since it
    is discouraged. For larger imports, you should use the Bulk
    API instead.

    For more details see: https://anaplan.docs.apiary.io/#UpdateModuleCellData.
    :param module_id: The ID of the Module.
    :param data: The data to write to the Module.
    :return: The number of cells changed or the response with the according error details.
    """
    client = anaplan_sdk.Client(
        auth=ctx.lifespan_context["auth"], workspace_id=workspace_id, model_id=model_id
    )
    result = client.tr.update_module_data(module_id=module_id, data=data)
    if isinstance(result, int):
        return str(result)
    return json.dumps(result)


if __name__ == "__main__":
    mcp.run()
