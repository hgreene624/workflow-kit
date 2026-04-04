# SDK Version Verification (Before First Deploy)

For Python services, before the first VPS `docker compose build`:

1. Check `requirements.txt` — are versions pinned or using `>=`?
2. If `>=`, pin them NOW: `pip freeze > requirements.txt` from a working local env, commit, and push
3. Compare the installed version locally vs what Docker will install (check PyPI for latest)
4. For MCP SDK specifically: verify `from mcp.server.fastmcp import FastMCP` works in the Docker image before starting the service — run:
   ```bash
   docker run --rm --entrypoint python3 <image> -c "from mcp.server.fastmcp import FastMCP; print('OK')"
   ```

## Why This Exists

{{ORG}}DB MCP sprint: Workers developed against MCP SDK v1.9 locally, but `mcp>=1.9.0` in requirements.txt caused Docker to install v1.26.0 which moved `@server.tool()` from `Server` to `FastMCP`. Three consecutive fix commits were needed at deploy time to resolve the API mismatch.
