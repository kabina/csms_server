#!/bin/bash
export SOCK_PORT=8765
export DB_USER=csms
export DB_PASSWORD=1q2w3e4r
export DB_HOST=juha.iptime.org
export DB_PORT=5432
export DB_SEVER=csms

/home/kabina/venv/csms/bin/python csms_server.py
