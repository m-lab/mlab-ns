#! /usr/bin/env bash

while true; do
  python ./remote_update.py -f "./test/remote_update.txt"
  sleep 600
done
