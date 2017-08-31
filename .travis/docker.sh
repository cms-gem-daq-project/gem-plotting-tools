#!/bin/sh -xe

# Thanks to:
# https://djw8605.github.io/2016/05/03/building-centos-packages-on-travisci/
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

# Version of CentOS/RHEL
el_version=$1
# need a varaible to point to the .travis directory
# Run tests in Container
if [ "$el_version" = "6" ]
then
    echo "Running SLC6 GEM DAQ custom docker image"
    docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker:slc6
    # docker_image=cern/slc6-base
    ls -l
    sudo docker run --rm=true -v `pwd`:/gem-plotting-tools:rw --entrypoint="/bin/bash" ${docker_image} -xec "echo Testing build on slc6;
  . /gem-plotting-tools/.travis/test_on_docker.sh ${OS_VERSION} ${PY_VER};
  echo -ne \"------\nEND gem-plotting-tools TESTS\n\";"
elif [ "$el_version" = "7" ]
then
    echo "Running CC7 GEM DAQ custom docker image"
    docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker:cc7
    # docker_image=cern/cc7-base
    ls -l
    docker run --privileged -d -ti -e "container=docker"  -v /sys/fs/cgroup:/sys/fs/cgroup -v `pwd`:/gem-plotting-tools:rw $docker_image /usr/sbin/init
    DOCKER_CONTAINER_ID=$(docker ps | grep "gemdaq_ci_worker:cc7" | awk '{print $1}')
    docker logs $DOCKER_CONTAINER_ID
    docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -xec "echo Testing build on cc7;
  . /gem-plotting-tools/.travis/test_on_docker.sh ${OS_VERSION} ${PY_VER};
  echo -ne \"------\nEND gem-plotting-tools TESTS\n\";"
    docker ps -a
    docker stop $DOCKER_CONTAINER_ID
    docker rm -v $DOCKER_CONTAINER_ID
fi
