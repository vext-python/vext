#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR=$(dirname ${BASH_SOURCE[0]})
ENV=/tmp/vext-test-virtualenv

rm -fR "${ENV}"
virtualenv -q -p $(which python3) "${ENV}"
source $SCRIPT_DIR/_test-env.sh "${ENV}"
