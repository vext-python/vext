#!/bin/bash
for f in *.py; do python -munittest "${f%.py}" ; done
