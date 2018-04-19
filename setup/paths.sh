# Setup cmsgemos
# echo "Checking paths"

#export BUILD_HOME=<your path>/cmsgemos/../
if [ -z "$BUILD_HOME" ]
then
    echo "BUILD_HOME not set, please set BUILD_HOME to the directory above the root of your repository"
    echo " (export BUILD_HOME=<your path>/cmsgemos/../) and then rerun this script"
    return
fi

#export DATA_PATH=/<your>/<data>/<directory>
if [ -z "$DATA_PATH" ]
then
    echo "DATA_PATH not set, please set DATA_PATH to a directory where data files created by scan applications will be written"
    echo " (export DATA_PATH=<your>/<data>/<directory>/) and then rerun this script"
    return
fi

#export ELOG_PATH=/<your>/<elog>/<directory>
if [ -z "$ELOG_PATH" ]
then
    echo "ELOG_PATH not set, please set ELOG_PATH to a directory where data files created by scan applications will be written"
    echo " (export ELOG_PATH=<your>/<elog>/<directory>/) and then rerun this script"
    return
fi

# Checking GEM_PYTHON_PATH
if [ -z "$GEM_PYTHON_PATH" ]
then
    echo "GEM_PYTHON_PATH not set, please source \$BUILD_HOME/cmsgemos/setup/paths.sh"
    return
fi

# Export project
export GEM_PLOTTING_PROJECT=$BUILD_HOME/gem-plotting-tools

# Setup Path
export PATH=$PATH:$GEM_PLOTTING_PROJECT
export PATH=$PATH:$GEM_PLOTTING_PROJECT/macros

# Setup PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$GEM_PLOTTING_PROJECT

# Making detector channel maps
# echo "Checking Detector Channel Maps"
if [ ! -f $GEM_PLOTTING_PROJECT/mapping/longChannelMap.txt ]
then
    python $GEM_PLOTTING_PROJECT/mapping/buildMapFiles.py 
fi

# Setting python virtualenv
SYSTEM_INFO="$(uname -a)"

echo $SYSTEM_INFO
if [[ $SYSTEM_INFO == *"lxplus"* ]];
then
    source $GEM_PLOTTING_PROJECT/setup/createVirtualEnv.sh
elif [[ $SYSTEM_INFO == *"gem904"* ]];
then
    print gem904
    KERNEL_VER="$(uname -r)"
    if [[ $KERNEL_VER == *"2.6."* ]];
    then
        source /data/bigdisk/sw/venvs/slc6/default/bin/activate
    elif [[ $KERNEL_VER == *"3.10."* ]];
    then
        source /data/bigdisk/sw/venvs/cc7/default/bin/activate
    else
      echo "operating system not recognized"
      echo "virtualenv is not set"
    fi
fi

# Done
# echo GEM_PLOTTING_PROJECT $GEM_PLOTTING_PROJECT
# echo "Setup Complete"
