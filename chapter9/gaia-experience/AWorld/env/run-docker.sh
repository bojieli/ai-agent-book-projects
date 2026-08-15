#!/bin/sh
cd "$(dirname "$0")"

sh virtualpc-mcp/mcp_server/build-image.sh && \

sh gaia-mcp-server/build-image.sh && \

sh virtualpc-mcp/run-local.sh