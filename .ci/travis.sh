#!/bin/bash -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
OS_VERSION=$1
PY_VER=$2
DOCKER_IMAGE=$3
ROOT_VER=$4

DOCKER_CONTAINER_ID=$(docker ps | grep ${DOCKER_IMAGE} | awk '{print $1}')
docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -ec "echo running test job;
   . /home/daqbuild/gem-plotting-tools/.ci/test_on_docker.sh ${OS_VERSION} ${PY_VER} ${ROOT_VER};"

exit 0
