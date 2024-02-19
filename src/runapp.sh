#!/bin/bash
export API_KEY=fmvGcA0N4w3IFHwnr56ba2hC1Ef9Is451JyF6LOD
export DB_USER=csms
export DB_PASSWORD=1q2w3e4r
export DB_HOST=nheo.duckdns.org
export DB_PORT=5432
export DB_SEVER=csms

gunicorn --certfile=/config/nheo.duckdns.org.crt --keyfile=/config/nheo.duckdns.org.key -w 4 -b 0.0.0.0:5000 ev_rest:app
#gunicorn -w 4 -b 0.0.0.0:5000 ev_rest:app
