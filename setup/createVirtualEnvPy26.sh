#!/bin/zsh

#export BUILD_HOME=<your path>/cmsgemos/../
if [ -z "$BUILD_HOME" ]
then
    echo "BUILD_HOME not set, please set BUILD_HOME to the directory above the root of your repository"
    echo " (export BUILD_HOME=<your path>/cmsgemos/../) and then rerun this script"
    return
fi

VENV_BASE=$BUILD_HOME/venv/slc6/py26
if [ ! -d "$VENV_BASE" ]
then
    # make env
    mkdir -p $VENV_BASE
    echo VENV_BASE $VENV_BASE
    virtualenv $VENV_BASE -p python --system-site-packages
    source $VENV_BASE/bin/activate
    pip install -U -r $GEM_PLOTTING_PROJECT/requirements.txt

    # store env info
    uname -a 2>&1 | tee -a $VENV_BASE/venvInfo.txt 
    python --version 2>&1 | tee -a $VENV_BASE/venvInfo.txt 
    more $GEM_PLOTTING_PROJECT/requirements.txt 2>&1 | tee -a $VENV_BASE/venvInfo.txt
else
    source $VENV_BASE/bin/activate
    #echo "virtualenv info:"
    #more $VENV_BASE/venvInfo.txt
fi
