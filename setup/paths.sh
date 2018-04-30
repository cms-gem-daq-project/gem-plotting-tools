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
export PATH=$GEM_PLOTTING_PROJECT:$PATH
export PATH=$GEM_PLOTTING_PROJECT/macros:$PATH

# Setup PYTHONPATH
export PYTHONPATH=$GEM_PLOTTING_PROJECT/pkg:$PYTHONPATH

# Making detector channel maps
# echo "Checking Detector Channel Maps"
if [ ! -f $GEM_PLOTTING_PROJECT/mapping/longChannelMap.txt ]
then
    python $GEM_PLOTTING_PROJECT/mapping/buildMapFiles.py 
fi

# Done
# echo GEM_PLOTTING_PROJECT $GEM_PLOTTING_PROJECT
# echo "Setup Complete"
