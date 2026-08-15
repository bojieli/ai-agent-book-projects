#!/bin/bash

cd "$(dirname "$0")"

for i in */; do
    if [ -d "$i" ] && [ -f "$i/pyproject.toml" ]; then
        echo "Installing dependencies for $i"
        (cd "$i" && uv sync) &
    fi
done

wait