docker stop `docker ps | grep runapp | awk '{print $1}'`
docker rm `docker ps -a| grep runapp | awk '{print $1}'`
docker stop `docker ps | grep runsock | awk '{print $1}'`
docker rm `docker ps -a| grep runsock | awk '{print $1}'`
