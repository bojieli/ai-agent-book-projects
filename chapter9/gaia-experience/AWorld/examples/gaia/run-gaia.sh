#!/bin/bash
BASE_DIR=$(dirname "$(readlink -f "$0")")

cd $BASE_DIR

sh -c "cd ../../ && python setup.py install"

sh -c "cd cmd && aworld web"
