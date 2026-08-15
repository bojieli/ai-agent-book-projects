#!/bin/sh
cd "$(dirname "$0")"

dt=$(date +%Y%m%d%H%M%S)
img=gaia-mcp-server
version=$dt

docker build -t $img -t $img:$version -t $img:latest . && \

echo "✅ Build image success: $img:$version"

exit 0