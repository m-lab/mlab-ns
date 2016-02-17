#!/bin/sh

yapf --diff --exclude=../server/mlabns/third_party/* --recursive --style=google \
    ../server/mlabns/*