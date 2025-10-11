#!/bin/bash

# Test runner script for workflow validation tests

set -e

cd "$(dirname "$0")"

echo "=== Installing test dependencies ==="
python3 -m pip install -q -r requirements.txt

echo ""
echo "=== Running workflow validation tests ==="
python3 -m unittest discover -s workflows -p "test_*.py" -v

echo ""
echo "=== All tests completed ==="