#!/bin/bash -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
OS_VERSION=$1
PY_VER=$2
DOCKER_IMAGE=$3
COMMAND=$4

ls -lZ

sudo usermod -aG docker $USER

groups

# need a varaible to point to the .travis directory
# Run tests in Container
if [ "${COMMAND}" = "start" ]
then
    if [ "$OS_VERSION" = "6" ]
    then
        echo "Starting SLC6 GEM DAQ custom docker image"
        # docker run -d --user daqbuild --rm=true -v `pwd`:/home/daqbuild/gem-plotting-tools:rw,z --entrypoint="/bin/bash" \
        docker run --user daqbuild --privileged -d -ti -e "container=docker" -v \
               `pwd`:/home/daqbuild/gem-plotting-tools:rw,z \
               ${DOCKER_IMAGE} /bin/bash
    elif [ "$OS_VERSION" = "7" ]
    then
        echo "Starting CC7 GEM DAQ custom docker image"
        docker run --user daqbuild --privileged -d -ti -e "container=docker" \
               -v /sys/fs/cgroup:/sys/fs/cgroup \
               -v `pwd`:/home/daqbuild/gem-plotting-tools:rw,z \
               ${DOCKER_IMAGE} /usr/sbin/init
    elif [ "$OS_VERSION" = "8" ]
    then
        echo "Starting CC8 GEM DAQ custom docker image"
    fi

    DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
    echo DOCKER_CONTAINER_ID=${DOCKER_CONTAINER_ID}
    docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec "echo Testing build on docker for `cat /etc/system-release`"
    docker logs $DOCKER_CONTAINER_ID
else
    DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
    docker logs $DOCKER_CONTAINER_ID

    if [ "${COMMAND}" = "stop" ]
    then
        docker exec -ti ${DOCKER_CONTAINER_ID} /bin/bash -ec 'echo -ne "------\nEND gem-plotting-tools TESTS\n";'
        docker stop $DOCKER_CONTAINER_ID
        docker rm -v $DOCKER_CONTAINER_ID
    elif [ "${COMMAND}" = "other" ]
    then
        docker ps -a
    fi
fi

docker ps -a

exit 0
