#!/bin/bash

# Gunicorn 프로세스 찾기
GUNICORN_PID=$(pgrep gunicorn)

# Gunicorn 프로세스 Kill
if [ -n "$GUNICORN_PID" ]; then
  # Gunicorn 프로세스가 실행 중인 경우 종료
  echo "Stopping Gunicorn (PID: $GUNICORN_PID)..."
  kill -SIGTERM $GUNICORN_PID
  sleep 5  # 여분의 시간을 줌
else
  echo "No running Gunicorn process found."
fi
