#!/bin/sh
cd "$(dirname "$0")"

sh ../virtualpc-mcp/mcp_server/build-image.sh && \

sh ../gaia-mcp-server/build-image.sh && \

sh -c "docker run -p 4242:4242 -p 5901:5901 --rm gaia-mcp-server"