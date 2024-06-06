#!/bin/bash

./precommit.sh

# Remove all stale log files
rm -rf ./src/data/logs/*.txt
rm -rf ./src/data/input/**/*.csv
rm -rf ./src/data/output/**/*.csv
