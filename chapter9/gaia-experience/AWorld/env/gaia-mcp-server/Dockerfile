FROM mcp-server-base:latest

COPY mcp_servers /app/mcp_servers

COPY docker/gaia_dataset /root/workspace/gaia_dataset

RUN sh /app/mcp_servers/init_env.sh