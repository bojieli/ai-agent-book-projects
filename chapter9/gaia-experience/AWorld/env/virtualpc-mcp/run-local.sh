#!/bin/sh
cd "$(dirname "$0")"

docker compose up --build --force-recreate -d