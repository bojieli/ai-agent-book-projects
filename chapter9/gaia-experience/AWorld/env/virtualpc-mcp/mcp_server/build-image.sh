#!/bin/sh

cd "$(dirname "$0")"

docker build -t mcp-server-base -f Dockerfile_mcp_server . && \

echo "✅ Build image success: mcp-server-base"
