#!/bin/bash -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
OS_VERSION=$1
PY_VER=$2
DOCKER_IMAGE=$3
ROOT_VER=$4
# need a varaible to point to the .travis directory
# Run tests in Container
# if [ "$OS_VERSION" = "6" ]
# then
#     echo "Running SLC6 GEM DAQ custom docker image"
#     docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker/extrapy/withroot:slc6
#     ls -lZ
#     sudo docker run --user daqbuild --rm=true -v `pwd`:/home/daqbuild/gem-plotting-tools:rw --entrypoint="/bin/bash" \
#          ${DOCKER_IMAGE} -ec "echo Testing build on slc6;
#   . /home/daqbuild/gem-plotting-tools/.travis/test_on_docker.sh ${OS_VERSION} ${PY_VER} ${ROOT_VER};
#   echo -ne \"------\nEND gem-plotting-tools TESTS\n\";"
# elif [ "$OS_VERSION" = "7" ]
# then
#     echo "Running CC7 GEM DAQ custom docker image"
#     docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker/extrapy/withroot:cc7
#     ls -lZ
#     docker run --user daqbuild --privileged -d -ti -e "container=docker"  -v /sys/fs/cgroup:/sys/fs/cgroup \
#            -v `pwd`:/home/daqbuild/gem-plotting-tools:rw ${DOCKER_IMAGE} /usr/sbin/init
#     DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
#     docker logs $DOCKER_CONTAINER_ID
#     docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -ec "echo Testing build on cc7;
#   . /home/daqbuild/gem-plotting-tools/.travis/test_on_docker.sh ${OS_VERSION} ${PY_VER} ${ROOT_VER};
#   echo -ne \"------\nEND gem-plotting-tools TESTS\n\";"
#     docker ps -a
#     docker stop $DOCKER_CONTAINER_ID
#     docker rm -v $DOCKER_CONTAINER_ID
# elif [ "$OS_VERSION" = "8" ]
# then
#     echo "Running CC8 GEM DAQ custom docker image"
# fi

DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -ec "echo running test job;
   . /home/daqbuild/gem-plotting-tools/.travis/test_on_docker.sh ${OS_VERSION} ${PY_VER} ${ROOT_VER};"

exit 0
