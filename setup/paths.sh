# Setup cmsgemos
echo "Checking paths" 

#export BUILD_HOME=<your path>/cmsgemos/../
if [[ -n "$BUILD_HOME" ]]; then
    echo BUILD_HOME $BUILD_HOME
else
    echo "BUILD_HOME not set, please set BUILD_HOME to the directory above the root of your repository"
    echo " (export BUILD_HOME=<your path>/cmsgemos/../) and then rerun this script"
    return
fi

#export DATA_PATH=/<your>/<data>/<directory>
if [[ -n "$DATA_PATH" ]]; then
    echo DATA_PATH $DATA_PATH
else
    echo "DATA_PATH not set, please set DATA_PATH to a directory where data files created by scan applications will be written"
    echo " (export DATA_PATH=<your>/<data>/<directory>/) and then rerun this script"
    return
fi

#export ELOG_PATH=/<your>/<elog>/<directory>
if [[ -n "$ELOG_PATH" ]]; then
    echo ELOG_PATH $ELOG_PATH
else
    echo "ELOG_PATH not set, please set ELOG_PATH to a directory where data files created by scan applications will be written"
    echo " (export ELOG_PATH=<your>/<elog>/<directory>/) and then rerun this script"
    return
fi

# Checking GEM_PYTHON_PATH
if [[ -n "$GEM_PYTHON_PATH" ]]; then
    echo GEM_PYTHON_PATH $GEM_PYTHON_PATH
else
    echo "GEM_PYTHON_PATH not set"
    echo "Setting up GEM_PYTHON_PATH"
    source $BUILD_HOME/cmsgemos/setup/paths.sh
fi

# Export project
export GEM_PLOTTING_PROJECT=$BUILD_HOME/gem-plotting-tools

# Setup Path
export PATH=$PATH:$GEM_PLOTTING_PROJECT
export PATH=$PATH:$GEM_PLOTTING_PROJECT/macros
export PATH=$PATH:$GEM_PLOTTING_PROJECT/setup

# Setup PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$BUILD_HOME/vfatqc-python-scripts
export PYTHONPATH=$PYTHONPATH:$GEM_PLOTTING_PROJECT
export PYTHONPATH=$PYTHONPATH:$GEM_PLOTTING_PROJECT/macros
export PYTHONPATH=$PYTHONPATH:$GEM_PLOTTING_PROJECT/setup

# Making detector channel maps
echo "Checking Detector Channel Maps"
if [ ! -f $GEM_PLOTTING_PROJECT/setup/longChannelMap.txt ]; then
	echo "No channel maps found, making"
	python $GEM_PLOTTING_PROJECT/setup/buildMapFiles.py 
fi

# Done
echo GEM_PLOTTING_PROJECT $GEM_PLOTTING_PROJECT
echo "Setup Complete"
