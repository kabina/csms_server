#!/bin/sh
export SOCK_SEVER=0.0.0.0
export SOCK_PORT=80
export DB_USER=csms
export DB_PASSWORD=1q2w3e4r
export DB_HOST=juha.iptime.org
export DB_PORT=5432
export DB_SEVER=csms

python csms_server.py
