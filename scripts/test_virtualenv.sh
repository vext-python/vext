#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

ENV=/tmp/vext-test-virtualenv

rm -fR "${ENV}"
virtualenv -q -p $(which python3) "${ENV}"
source _test-env.sh "${ENV}"
