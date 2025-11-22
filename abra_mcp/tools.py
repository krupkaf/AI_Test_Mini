"""MCP tools for Abra Gen API operations."""

import json
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .client import AbraClient, AbraAPIError

logger = logging.getLogger(__name__)


def register_tools(server: Server, client: AbraClient) -> None:
    """Register all MCP tools with the server.

    Args:
        server: MCP server instance
        client: Abra API client
    """

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools."""
        return [
            Tool(
                name="abra_query",
                description=(
                    "Execute a flexible query on any Abra Gen business object collection. "
                    "Supports filtering (where), field selection (select), sorting (orderby), "
                    "expanding related objects (expand), and pagination (skip/take). "
                    "Use this for custom queries on any collection like 'issuedinvoices', "
                    "'firms', 'storecards', etc."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection": {
                            "type": "string",
                            "description": (
                                "Business object collection name (e.g., 'issuedinvoices', 'firms', "
                                "'storecards', 'receivedorders', 'accounts')"
                            ),
                        },
                        "select": {
                            "type": "string",
                            "description": (
                                "Fields to return, comma-separated (e.g., 'ID,Code,Name' or "
                                "'ID,Amount,Firm_ID.Name'). Use '*' for all fields."
                            ),
                        },
                        "where": {
                            "type": "string",
                            "description": (
                                "Filter condition using Abra query language "
                                "(e.g., 'Amount gt 10000', 'Code eq \"ABC\"', "
                                "'Name like \"%test%\"')"
                            ),
                        },
                        "orderby": {
                            "type": "string",
                            "description": (
                                "Sorting specification (e.g., 'Amount desc', 'Name', "
                                "'Firm_ID.Code,Amount desc')"
                            ),
                        },
                        "expand": {
                            "type": "string",
                            "description": (
                                "Include related objects (e.g., 'Firm_ID', "
                                "'Firm_ID(ID,Name)', 'Rows')"
                            ),
                        },
                        "skip": {
                            "type": "integer",
                            "description": "Number of records to skip for pagination",
                        },
                        "take": {
                            "type": "integer",
                            "description": "Maximum number of records to return (limit)",
                        },
                    },
                    "required": ["collection"],
                },
            ),
            Tool(
                name="abra_get_resource",
                description=(
                    "Get a specific resource by ID from any Abra Gen collection. "
                    "Returns detailed information about a single business object. "
                    "Useful when you know the exact ID of the record you want to retrieve."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection": {
                            "type": "string",
                            "description": (
                                "Business object collection name (e.g., 'issuedinvoices', "
                                "'firms', 'storecards')"
                            ),
                        },
                        "resource_id": {
                            "type": "string",
                            "description": "ID of the resource to retrieve",
                        },
                        "expand": {
                            "type": "string",
                            "description": (
                                "Include related objects (e.g., 'Firm_ID', 'Rows', "
                                "'Firm_ID(ID,Name)')"
                            ),
                        },
                    },
                    "required": ["collection", "resource_id"],
                },
            ),
            Tool(
                name="abra_list_firms",
                description=(
                    "Get a list of firms/customers from Abra Gen. "
                    "Returns basic information including ID, code, name, and contact details. "
                    "Supports searching and pagination."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": (
                                "Search term to filter firms by name or code (case-insensitive)"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of results to skip for pagination (default: 0)",
                            "default": 0,
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="abra_list_invoices",
                description=(
                    "Get a list of issued invoices from Abra Gen. "
                    "Returns invoice details including number, amount, customer, and period. "
                    "Supports date filtering and pagination."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": (
                                "Start date for filtering (ISO format: YYYY-MM-DD or "
                                "ISO datetime: YYYY-MM-DDTHH:MM:SS)"
                            ),
                        },
                        "to_date": {
                            "type": "string",
                            "description": (
                                "End date for filtering (ISO format: YYYY-MM-DD or "
                                "ISO datetime: YYYY-MM-DDTHH:MM:SS)"
                            ),
                        },
                        "firm_id": {
                            "type": "string",
                            "description": "Filter by specific customer/firm ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of results to skip for pagination (default: 0)",
                            "default": 0,
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="abra_list_products",
                description=(
                    "Get a list of products/store cards from Abra Gen. "
                    "Returns product information including code, name, and EAN. "
                    "Supports searching and pagination."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": (
                                "Search term to filter products by name or code (case-insensitive)"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of results to skip for pagination (default: 0)",
                            "default": 0,
                        },
                    },
                    "required": [],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "abra_query":
                return await handle_abra_query(client, arguments)
            elif name == "abra_get_resource":
                return await handle_abra_get_resource(client, arguments)
            elif name == "abra_list_firms":
                return await handle_abra_list_firms(client, arguments)
            elif name == "abra_list_invoices":
                return await handle_abra_list_invoices(client, arguments)
            elif name == "abra_list_products":
                return await handle_abra_list_products(client, arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except AbraAPIError as e:
            logger.error(f"Abra API error in {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            logger.exception(f"Unexpected error in {name}")
            return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_abra_query(client: AbraClient, args: dict[str, Any]) -> list[TextContent]:
    """Handle abra_query tool."""
    collection = args["collection"]
    select = args.get("select")
    where = args.get("where")
    orderby = args.get("orderby")
    expand = args.get("expand")
    skip = args.get("skip")
    take = args.get("take")

    logger.info(f"Query {collection}: select={select}, where={where}")

    result = await client.query(
        collection=collection,
        select=select,
        where=where,
        orderby=orderby,
        expand=expand,
        skip=skip,
        take=take,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {"collection": collection, "count": len(result), "results": result}, indent=2
            ),
        )
    ]


async def handle_abra_get_resource(
    client: AbraClient, args: dict[str, Any]
) -> list[TextContent]:
    """Handle abra_get_resource tool."""
    collection = args["collection"]
    resource_id = args["resource_id"]
    expand = args.get("expand")

    logger.info(f"Get {collection}/{resource_id}")

    params: dict[str, Any] = {}
    if expand:
        params["expand"] = expand

    result = await client.get(collection, resource_id=resource_id, params=params)

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_abra_list_firms(client: AbraClient, args: dict[str, Any]) -> list[TextContent]:
    """Handle abra_list_firms tool."""
    search = args.get("search")
    limit = args.get("limit", 50)
    offset = args.get("offset", 0)

    logger.info(f"List firms: search={search}, limit={limit}, offset={offset}")

    # Build where clause for search
    where: Optional[str] = None
    if search:
        # Search in both name and code (case-insensitive)
        where = f"(upper(Name) like upper('%{search}%') or upper(Code) like upper('%{search}%'))"

    result = await client.query(
        collection="firms",
        select="ID,Code,Name,Email,Phone",
        where=where,
        orderby="Name",
        skip=offset,
        take=limit,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps({"collection": "firms", "count": len(result), "firms": result}, indent=2),
        )
    ]


async def handle_abra_list_invoices(
    client: AbraClient, args: dict[str, Any]
) -> list[TextContent]:
    """Handle abra_list_invoices tool."""
    from_date = args.get("from_date")
    to_date = args.get("to_date")
    firm_id = args.get("firm_id")
    limit = args.get("limit", 50)
    offset = args.get("offset", 0)

    logger.info(f"List invoices: from={from_date}, to={to_date}, firm={firm_id}")

    # Build where clause
    where_conditions = []
    if from_date:
        where_conditions.append(f"DocDate ge timestamp'{from_date}'")
    if to_date:
        where_conditions.append(f"DocDate le timestamp'{to_date}'")
    if firm_id:
        where_conditions.append(f"Firm_ID eq '{firm_id}'")

    where = " and ".join(where_conditions) if where_conditions else None

    result = await client.query(
        collection="issuedinvoices",
        select="ID,OrdNumber,Amount,DocDate,Firm_ID.Name",
        where=where,
        orderby="OrdNumber desc",
        expand="Firm_ID",
        skip=offset,
        take=limit,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {"collection": "issuedinvoices", "count": len(result), "invoices": result}, indent=2
            ),
        )
    ]


async def handle_abra_list_products(
    client: AbraClient, args: dict[str, Any]
) -> list[TextContent]:
    """Handle abra_list_products tool."""
    search = args.get("search")
    limit = args.get("limit", 50)
    offset = args.get("offset", 0)

    logger.info(f"List products: search={search}, limit={limit}, offset={offset}")

    # Build where clause for search
    where: Optional[str] = None
    if search:
        # Search in both name and code (case-insensitive)
        where = f"(upper(Name) like upper('%{search}%') or upper(Code) like upper('%{search}%'))"

    result = await client.query(
        collection="storecards",
        select="ID,Code,Name,EAN",
        where=where,
        orderby="Code",
        skip=offset,
        take=limit,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {"collection": "storecards", "count": len(result), "products": result}, indent=2
            ),
        )
    ]
