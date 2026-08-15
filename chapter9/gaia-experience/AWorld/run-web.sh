#!/bin/sh
BASE_DIR=$(dirname "$(readlink -f "$0")")

cd $BASE_DIR

sh -c "cd aworld/cmd/web && npm install && npm run build"

python setup.py install

cd examples/web && aworld web
