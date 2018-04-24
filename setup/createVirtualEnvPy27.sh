#!/bin/zsh

#export BUILD_HOME=<your path>/cmsgemos/../
if [ -z "$BUILD_HOME" ]
then
    echo "BUILD_HOME not set, please set BUILD_HOME to the directory above the root of your repository"
    echo " (export BUILD_HOME=<your path>/cmsgemos/../) and then rerun this script"
    return
fi

VENV_BASE=$BUILD_HOME/venv/slc6/py27
if [ ! -d "$VENV_BASE" ]
then
    # make env
    mkdir -p $VENV_BASE
    source /opt/rh/python27/enable
    export PYTHONDIR=/opt/rh/python27/root/usr
    export PYTHONPATH=$PYTHONPATH:$ROOTSYS/lib
    export LD_LIBRARY_PATH=$ROOTSYS/lib:$PYTHONDIR/lib:$LD_LIBRARY_PATH:/opt/rh/python27/root/usr/lib64
    echo VENV_BASE $VENV_BASE
    virtualenv $VENV_BASE -p python --system-site-packages
    source $VENV_BASE/bin/activate
    pip install -U -r $GEM_PLOTTING_PROJECT/requirements.txt

    # pip doesn't seem to be smart enough to resolve wheel dependencies for root_numpy
    # see: https://github.com/scikit-hep/root_numpy/issues/277
    # following hack found to work
    pip uninstall --yes root_numpy
    cd /tmp
    git clone git://github.com/rootpy/root_numpy.git
    cd root_numpy
    python setup.py install
    cd $BUILD_HOME

    # store env info
    uname -a 2>&1 | tee -a $VENV_BASE/venvInfo.txt 
    python --version 2>&1 | tee -a $VENV_BASE/venvInfo.txt 
    more $GEM_PLOTTING_PROJECT/requirements.txt 2>&1 | tee -a $VENV_BASE/venvInfo.txt
else
    source /opt/rh/python27/enable
    export PYTHONDIR=/opt/rh/python27/root/usr
    export PYTHONPATH=$PYTHONPATH:$ROOTSYS/lib
    export LD_LIBRARY_PATH=$ROOTSYS/lib:$PYTHONDIR/lib:$LD_LIBRARY_PATH:/opt/rh/python27/root/usr/lib64
    source $VENV_BASE/bin/activate
    #echo "virtualenv info:"
    #more $VENV_BASE/venvInfo.txt
fi
