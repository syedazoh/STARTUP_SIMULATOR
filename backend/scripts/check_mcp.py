"""Official SDK client: privately prompt for an owner-minted capability."""

import asyncio
import getpass
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    resource = os.environ.get("MCP_RESOURCE_URL", "http://localhost:8000/mcp/")
    token = getpass.getpass("MCP capability (hidden): ")
    if not token:
        raise SystemExit("No capability supplied")
    async with streamable_http_client(
        resource, headers={"Authorization": "Bearer " + token}
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(
                "Connected tools:",
                ", ".join(t.name for t in (await session.list_tools()).tools),
            )


if __name__ == "__main__":
    asyncio.run(main())
