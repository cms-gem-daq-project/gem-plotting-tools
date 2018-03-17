#!/bin/bash -xe

# Thanks to:
# https://github.com/opensciencegrid/htcondor-ce/tree/master/tests

OS_VERSION=$1
PY_VER=$2
ROOT_VER=$3

echo OS_VERSION $OS_VERSION
echo PY_VER $PY_VER
echo ROOT_VER $ROOT_VER

ls -l $PWD

# Clean the yum cache
# yum -y clean all
# yum -y clean expire-cache
# yum -y install root root-\*

yum -y install man

uname -a
whoami

export BUILD_HOME=/home/daqbuild
export DATA_PATH=/data

# set up ROOT
# v5.34.28-gcc5.1
len=${#ROOT_VER}
gccver=${ROOT_VER:$((${len}-3)):3}
rootver=${ROOT_VER:0:$((${len}-7))}

cd /opt/root/${rootver}-gcc${gccver}/root
ls -lZ
. ./bin/thisroot.sh
# elif [ "$OS_VERSION" = "7" ]
# then
#     cd /opt/root/${rootver}-gcc${gccver}/root
#     ls -lZ
#     . ./bin/thisroot.sh
# fi

cd ${BUILD_HOME}/gem-plotting-tools
# git clone https://github.com/cms-gem-daq-project/gembuild.git config

pyexec=$(which ${PY_VER})
echo Trying to test with ${pyexec}
if [ -f "$pyexec" ]
then
    virtualenv ~/virtualenvs/${PY_VER} -p ${pyexec} --system-site-packages
    . ~/virtualenvs/${PY_VER}/bin/activate
    numver=$(python -c "import distutils.sysconfig;print(distutils.sysconfig.get_python_version())")
    pip install -U pip
    pip install -U --no-install -r requirements.txt
    # pip install -U root_numpy
    pip install codecov
    python -c "import pkg_resources; print(pkg_resources.get_distribution('setuptools'))"
    # if [ ${OS_VERSION}="6" ]
    # then
    pip install importlib
    # fi

    pip install -U setuptools

    python -c "import pkg_resources; print(pkg_resources.get_distribution('setuptools'))"
    python -c "import pkg_resources; print(pkg_resources.get_distribution('pip'))"

    make

    make rpm

    # coverage run python
    # codecov
    # bash <(curl -s https://codecov.io/bash) && echo "Uploaded code coverage"
    deactivate
fi

exit 0
