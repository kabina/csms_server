docker stop `docker ps | grep runapp | awk '{print $1}'`
docker rm `docker ps -a| grep runapp | awk '{print $1}'`
docker run -d -p 5000:5000 kabina/csms-server:latest
docker stop `docker ps | grep runsock | awk '{print $1}'`
docker rm `docker ps -a| grep runsock | awk '{print $1}'`
docker run -d -p 8765:8765 kabina/socket-server:latest
