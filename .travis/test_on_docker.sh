#!/bin/sh -xe

# Thanks to:
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

OS_VERSION=$1
PY_VER=$2

echo OS_VERSION $OS_VERSION
echo PY_VER $PY_VER

ls -l $PWD

# Clean the yum cache
yum -y clean all
yum -y clean expire-cache

uname -a

export BUILD_HOME=$PWD

cd ${BUILD_HOME}/gem-plotting-tools

pyexec=$(which ${PY_VER})

if [ -f "$pyexec" ]
then
    virtualenv ~/virtualenvs/${PY_VER} -p ${pyver} --system-site-packages
    . ~/virtualenvs/${PY_VER}/bin/activate
    pip install -r requirements.txt
    pip install codecov
fi
