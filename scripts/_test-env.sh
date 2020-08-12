#!/bin/bash

# Test the python envs, such as virtualenv, venv and PipEnv
#    Initially verify that modules cannot be imported,
#    then install vext verify they *can* be imported.
#
# Prerequisites:
#    System environment with the correct dependencies installed.
#
#
# Create environment seperately, then with path to environment:
# $ virtualenv env
# $ _test_env.sh env
#
# Wrapper scripts that handle environment creation are provided,
# e.g. test_virtualenv.sh
#
set -euo pipefail
IFS=$'\n\t'

ENV=$1
if [[ "" ==  "$ENV" ]]; then
  echo "Pass location of python virtualenv to create"
  exit 1
fi

PROJECT_DIR=$(realpath $(dirname ${BASH_SOURCE[0]})/..)
PYTHON="${ENV}/bin/python"
VEXT="${ENV}/bin/vext"
PIP="${ENV}/bin/pip"

# Full list of vext packages:
# vext.gi vext.pygtk vext.pyqt4 vext.pyqt5 vext.wx vext.pygame vext.panda3d vext.vtk vext.libtorrent

# TODO list of modules is not complete.
if /usr/bin/python3 --version | grep -q "Python 3"; then
 declare -a MODULES=(\
  "gi"\
  "libtorrent"\
  "pygame"\
 )
else
 declare -a MODULES=(\
  "gi"\
  "pygame"\
 )
fi

declare -a PACKAGES=(\
 "vext.gi"\
 "vext.libtorrent"\
 "vext.panda3d"\
 "vext.pygtk"\
 "vext.pyqt4"\
 "vext.pyqt5"\
 "vext.panda3d"\
 "vext.pygame"\
 "vext.vtk"\
 "vext.wx"\
)


function build_and_install_vext() {
  $PIP install $PROJECT_DIR > /dev/null
}

function install_packages() {
  $PIP install "${PACKAGES[@]}" > /dev/null
}

function test_modules_cannot_be_imported() {
  # When the environment has been setup initially, but nothing
  # has been installed imports should fail.
  echo "Initial environment: modules should not be importable."
  export ERR=0
  for module in "${MODULES[@]}" ; do
    if "$PYTHON" -c "import $module" 2&> /dev/null; then
      echo "Test initial setup cannot import $module (fail)"
      export ERR=1
    else
      echo "Test initial setup cannot import $module (pass)"
    fi
  done
}

function test_modules_can_be_imported() {
  # When the environment has been setup initially, and
  # vext and it's modules are installed, imports should
  # succeed.
  echo "Inside python env: modules should be importable."
  export ERR=0
  for module in "${MODULES[@]}" ; do
    echo "$PYTHON" -c "import $module"
    if "$PYTHON" -c "import $module"; then
      echo "Test import $module (pass)"
    else
      export ERR=1
      echo "Test import $module (fail)"
    fi
  done
}

function test_vext_module_check() {
  # When the environment has been setup initially, and
  # vext and it's modules are installed, vexts own
  # import check should pass.
  echo "Vext module check."
  export ERR=0
  for module in "${MODULES[@]}" ; do
    if ! $VEXT -c $module.vext 2&> /dev/null; then
      echo "Test vext $module installed (pass)"
    else
      echo "Test import $module installed (fail)"
      export ERR=1
    fi
  done
}


function run_unittests() {
  cd $PROJECT_DIR/tests
  python -munittest test*.py
  exit $?
}

if [ "${CI:-default}" == "true" ]; then
  set -x
fi

# Sanity check initial environment:
test_modules_cannot_be_imported

# Install everything
build_and_install_vext
install_packages

# Test the environment
test_modules_can_be_imported
test_vext_module_check

run_unittests

exit $ERR
