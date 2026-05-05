import json
import os
from contextlib import asynccontextmanager
import keyring
from typing import Any, Annotated

import anaplan_sdk
from anaplan_sdk.models import (
    LineItem,
    User,
    View
)
from dotenv import load_dotenv
from fastmcp import Context, FastMCP

load_dotenv()

CATALOG: dict[str, dict] = {
    "get_processes": {
        "description": "Return all processes in an Anaplan model. Processes combine import, export, delete, or sort actions in sequence.",
        "tags": ["action", "process", "bulk"],
        "annotations": {
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
            "openWorldHint": True
        },
        "params": {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan workspace containing the model. Defaults to WORKSPACE_ID env var.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan model containing processes. Defaults to MODEL_ID env var.",
            },
        },
    },
    "get_imports": {
        "description": "Return all import actions in an Anaplan model. Import actions load data from files or views into a list or module.",
        "tags": ["action", "import", "bulk"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan workspace containint the model.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan model containing imports.",
            },
        },
    },
    "get_exports": {
        "description": "Return all export actions in an Anaplan model. Export actions write data from modules or lists to a file.",
        "tags": ["action", "export", "bulk"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan workspace containint the model.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan model containing exports.",
            },
        },
    },
    "get_workspaces": {
        "description": "Return all Anaplan workspaces the user can access.",
        "tags": ["workspace"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "search_pattern": {
                "type": "string",
                "required": False,
                "description": "Case-insensitive substring filter. Supports % and _ wildcards. Requires Tenant Admin role.",
            },
        },
    },
    "get_models": {
        "description": "Return all Anaplan models, optionally filtered to a single workspace.",
        "tags": ["model"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "ID for Anaplan workspace containing models.",
            },
            "only_in_workspace": {
                "type": "boolean",
                "required": False,
                "description": "If True, only lists models in the specified workspace. Default: False.",
            },
            "search_pattern": {
                "type": "string",
                "required": False,
                "description": "Optional name filter. Supports % and _ wildcards. Requires Tenant Admin role.",
            },
        },
    },
    "get_modules": {
        "description": "Return all modules in an Anaplan model. Modules contain line items and cells.",
        "tags": ["module", "transactional"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan model ID.",
            },
        },
    },
    "get_views": {
        "description": "Return all views in an Anaplan model. Views organize module dimensions and may filter data.",
        "tags": ["view", "transactional"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan model ID.",
            },
        },
    },
    "get_line_items": {
        "description": "Return all the line items in an Anaplan model. If the module ID is specified, only show the line items for that module.",
        "tags": ["line_item", "transactional"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "workspace_id": {
                "type": "string",
                "required": True,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": True,
                "description": "Anaplan model ID.",
            },
            "module_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan module ID.",
            },
        },
    },
    "run_action": {
        "description": "Run an Anaplan action by numeric ID. Supports imports, exports, processes, delete, optimize, and sort. Not recommended for file-based imports/exports or processes that include file operations.",
        "tags": ["action", "bulk"],
        "annotations": {"readOnlyHint": False, "idempotentHint": False, "destructiveHint": True,
            "openWorldHint": True},
        "params": {
            "action_id": {
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the Anaplan action to run.",
            },
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan model ID.",
            },
        },
    },
    "export_and_download": {
        "description": "Run an Anaplan export action and download the resulting file. Use for export actions only — not for processes.",
        "tags": ["action", "export", "bulk"],
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False,
            "openWorldHint": True},
        "params": {
            "export_id": {
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the export action.",
            },
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan model ID.",
            },
        },
    },
    "upload_and_import": {
        "description": "Upload file content to Anaplan and run an import action. Use for import actions only — not for processes.",
        "tags": ["action", "import", "bulk"],
        "annotations": {"readOnlyHint": False, "idempotentHint": False, "destructiveHint": True,
            "openWorldHint": True},
        "params": {
            "file_id": {
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the Anaplan file to upload to.",
            },
            "content": {
                "type": "string",
                "required": True,
                "description": "File content to upload.",
            },
            "import_id": {
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the import action to run.",
            },
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan model ID.",
            },
        },
    },
    "update_module_data": {
        "description": "Write data to an Anaplan module transactionally. Max 100,000 cells or 15 MB per request. For larger updates use upload_and_import instead.",
        "tags": ["update", "transactional"],
        "annotations": {"readOnlyHint": False, "idempotentHint": False, "destructiveHint": True,
            "openWorldHint": True},
        "params": {
            "module_id": {
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the module to update.",
            },
            "data": {
                "type": "array",
                "required": True,
                "description": "List of cell update objects. See https://anaplan.docs.apiary.io/#UpdateModuleCellData.",
                "items": {
                    "properties": {
                        "lineItemId": {
                            "type": "string"
                        },
                        "dimensions": {
                            "items": {
                                "properties": {
                                    "dimensionId": {
                                        "type": "string"
                                    },
                                    "itemId": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "dimensionId",
                                    "itemId"
                                ],
                                "type": "object"
                            },
                            "type": "array"
                        },
                        "value": {
                            "anyOf": [
                                {
                                    "type": "integer"
                                },
                                {
                                    "type": "string"
                                }
                            ],
                            "title": "Value"
                        }
                    },
                    "required": [
                        "lineItemId",
                        "dimensions",
                        "value"
                    ],
                    "type": "object"
                }
            },
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan workspace ID.",
            },
            "model_id": {
                "type": "string",
                "required": False,
                "description": "Anaplan model ID.",
            },
        },
    },
}


def _score_catalog(intent: str, top_n: int = 5) -> list[dict]:
    tokens = set(intent.lower().split())
    scored = []
    for action_id, entry in CATALOG.items():
        text = (entry["description"] + " " + " ".join(entry["tags"])).lower()
        score = sum(1 for t in tokens if t in text)
        scored.append((score, action_id, entry))
    scored.sort(key=lambda x: -x[0])
    if not scored or scored[0][0] == 0:
        return [
            {
                "id": k,
                "description": v["description"],
                "tags": v["tags"],
                "annotations": v.get("annotations", {}),
                "params": v["params"],
            }
            for k, v in CATALOG.items()
        ]
    return [
        {
            "id": aid,
            "description": e["description"],
            "tags": e["tags"],
            "annotations": e.get("annotations", {}),
            "params": e["params"],
        }
        for score, aid, e in scored[:top_n]
        if score > 0
    ]


def _build_auth() -> anaplan_sdk.AnaplanRefreshTokenAuth:
    client_id = os.environ["ANAPLAN_CLIENT_ID"]
    client_secret = os.environ["ANAPLAN_CLIENT_SECRET"]
    redirect_uri = os.environ["ANAPLAN_REDIRECT_URI"]
    part_a = keyring.get_password("Anaplan_a", os.getlogin ())
    part_b = keyring.get_password("Anaplan_b", os.getlogin ())
    json_str = part_a + part_b  # windows workaround
    token = json.loads(json_str)
    return anaplan_sdk.AnaplanRefreshTokenAuth(
        client_id, client_secret, redirect_uri, token
    )


@asynccontextmanager
async def lifespan(server: FastMCP):
    auth = _build_auth()
    yield {
        "auth": auth
    }


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
    """,
)


@mcp.tool(
    title="Who am I",
    description="Return information about the currently authenticated Anaplan user.",
    tags={"user", "integration", "transactional"},
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": True
    },
)
async def me(ctx: Context) -> User:
    client = anaplan_sdk.AsyncClient(
        auth = ctx.lifespan_context["auth"]
    )
    result = await client.audit.get_user()
    return result

@mcp.tool (
    title="Read view data",
    description="retrieve the cell data for a view. You can either query for the default page, or provide page selectors to query for other pages. This call returns data as JSON.",
    tags={"read", "integration", "transactional"},
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": True
    },
)
async def get_view_data (
          view_id: Annotated[int, "ID of the view containing data to read."],
          workspace_id: Annotated[str, "ID of Anaplan workspace containing the model."],
          model_id: Annotated[str, "ID of the Anaplan model containing the view."],
          ctx: Context
) -> dict[str, Any]:
    """Get view data as JSON.

    :param view_id: the ID of a view or module to export
    :param workspace_id: the workspace containing this model
    :param model_id: the model containing this view
    """
    headers = {
        "accept": "application/json"
    }
    client = anaplan_sdk.AsyncClient(
        auth = ctx.lifespan_context["auth"],
        workspace_id=workspace_id,
        model_id=model_id
    )
    res = await client._http.get (
        f"{client._url}/views/{view_id}/data?format=v1",
        headers=headers
    )
    return res

@mcp.tool (
    title="Get information about a view",
    description="Use this call to retrieve the name, IDs, and lists of names for the dimensions (columns, pages, rows) on a specified view.",
    tags={"view", "integration", "transactional"},
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": True
    },
)
async def get_view_info (
          view_id: Annotated[int, "ID of the view."],
          workspace_id: Annotated[str, "ID of Anaplan workspace containing the model."],
          model_id: Annotated[str, "ID of the Anaplan model containing the view."],
          ctx: Context
) -> dict[str, Any]:
    """Get view data as JSON.

    :param view_id: the ID of a view or module to export
    :param workspace_id: the workspace containing this model
    :param model_id: the model containing this view
    """
    client = anaplan_sdk.AsyncClient(
        auth = ctx.lifespan_context["auth"],
        workspace_id=workspace_id,
        model_id=model_id
    )
    res = await client._http.get (
        f"{client._url}/views/{view_id}"
    )
    return res

  


@mcp.tool(
    title="Search Anaplan actions",
    description="Search the Anaplan action catalog by natural language intent.",
    tags={"catalog", "integration"},
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False
    },
)
def search_actions(
        intent: Annotated[str, "Natural language description of what you want to do."]
) -> str:
    """Search the Anaplan action catalog by natural language intent.

    Returns matching action IDs, descriptions, and parameter schemas.
    Use execute_action to run a chosen action.

    :param intent: Natural language description of what you want to do.
    """
    return json.dumps(_score_catalog(intent), indent=2)


@mcp.tool(
    title="Run selected Anaplan action",
    description="Execute a catalog action by its ID with the given parameters.",
    tags={"catalog", "integration"},
    annotations={
        "openWorldHint": False
    },
)
async def execute_action(
        catalog_action: Annotated[str, "Action ID returned by search_actions"],
        params: Annotated[dict[str, Any], "Parameters dict matching the action's schema"],
        ctx: Context
) -> Any:
    """Execute a catalog action by its ID with the given parameters.

    Use search_actions to discover available action IDs and their parameter schemas.

    :param catalog_action: Action ID returned by search_actions.
    :param params: Parameters dict matching the action's schema.
    """
    if catalog_action not in CATALOG:
        return json.dumps(
            {
                "isError": True,
                "message": f"Unknown action '{catalog_action}'. Use search_actions to find valid IDs.",
            }
        )

    auth = ctx.lifespan_context["auth"]
    workspace_id = params.get("workspace_id", os.environ["WORKSPACE_ID"])
    model_id = params.get("model_id", os.environ["MODEL_ID"])

    match catalog_action:
        case "get_processes":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            return json.dumps([p.model_dump() for p in await client.get_processes()])
        case "get_imports":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            return json.dumps([p.model_dump() for p in await client.get_imports()])
        case "get_exports":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            return json.dumps([p.model_dump() for p in await client.get_exports()])
        case "get_workspaces":
            client = anaplan_sdk.AsyncClient(auth=auth)
            return json.dumps(
                [
                    ws.model_dump()
                    for ws in await client.get_workspaces(
                        search_pattern=params.get("search_pattern")
                    )
                ]
            )
        case "get_models":
            client = anaplan_sdk.AsyncClient(auth=auth, workspace_id=workspace_id)
            return json.dumps(
                [
                    m.model_dump()
                    for m in await client.get_models(
                        only_in_workspace=params.get("only_in_workspace", False),
                        search_pattern=params.get("search_pattern"),
                    )
                ]
            )
        case "get_modules":
            client = anaplan_sdk.AsyncClient(auth=auth, workspace_id=workspace_id, model_id=model_id)
            return json.dumps([m.model_dump() for m in await client.tr.get_modules()])
        case "get_views":
            client = anaplan_sdk.AsyncClient(auth=auth, workspace_id=workspace_id, model_id=model_id)
            #return json.dumps([m.model_dump() for m in await client.tr.get_views()])
            result:list[View] = await client.tr.get_views()
            return result
        case "run_action":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            result = await client.run_action(params["action_id"])
            return json.dumps(result.model_dump())
        case "export_and_download":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            return await client.export_and_download(params["export_id"])
        case "upload_and_import":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            result = await client.upload_and_import(
                file_id=params["file_id"],
                content=params["content"],
                action_id=params["import_id"],
            )
            return json.dumps(result.model_dump())
        case "update_module_data":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            result = await client.tr.update_module_data(
                module_id=params["module_id"],
                data=params["data"],
            )
            if isinstance(result, int):
                return str(result)
            return json.dumps(result)
        case "get_line_items":
            client = anaplan_sdk.AsyncClient(
                auth=auth, workspace_id=workspace_id, model_id=model_id
            )
            result:list[LineItem] = await client.tr.get_line_items(
                only_module_id=params["module_id"]
            )
            return result


if __name__ == "__main__":
    mcp.run()
