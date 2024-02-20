#!/bin/bash

# Set the target URL to scan
TARGET_URL=https://nheo.duckdns.org:5000

# Start ZAP
zap-cli --zap-url 0.0.0.0 --port 8080 &

# Wait for ZAP to start
sleep 10

# Set the context for the scan
zap-cli context new ZAP-Dast-Scan

# Import the context
zap-cli context import ZAP-Dast-Scan context.xml

# Scan the target URL
zap-cli scan.run -u $TARGET_URL

# Generate the report
zap-cli report -f markdown -o report.md

# Stop ZAP
killall zap-api
