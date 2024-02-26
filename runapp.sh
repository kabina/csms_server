#!/bin/bash

/home/kabina/venv/csms/bin/gunicorn -w 4 -b 0.0.0.0:5000 ev_rest:app
