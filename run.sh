docker ps | grep csms-server | awk '{print $1}' | xargs -r docker stop
docker ps -a | grep csms-server | awk '{print $1}' | xargs -r docker rm
docker images | grep csms-server | awk '{print $3}' | xargs -r docker rmi
docker run -d --name "csms-server" -v /var/gitlab/config/ssl:/config -p 192.168.0.108:5000:443 kabina/csms-server:latest
docker ps | grep socket-server | awk '{print $1}' | xargs -r docker stop
docker ps -a | grep socket-server | awk '{print $1}' | xargs -r docker rm
docker images | grep socket-server | awk '{print $3}' | xargs -r docker rmi
docker run -d --name "socket-server" -p 192.168.0.108:8765:80 kabina/socket-server:latest
