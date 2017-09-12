#!/bin/bash
usage() {
    echo 'Usage : ./gemPlotterAllChannels.sh <InFile> <anaType> <branchName>'
    echo '          InFile: tab delimited input file, first line is "ChamberName\tscandate\tIndepVarName"'
    echo '                  subseuqent lines are values for: "ChamberName\tscandate\tIndepVarValue", e.g.:'
    echo '                  GE11-VI-L-CERN-0002 2017.09.04.20.12    1'
    echo ''
    echo '          anaType: type of analysis to perform, see tree_names.keys() of anaInfo.py'
    echo ''
    echo '          branchName: TName of the TBranch whose data will be plotted against IndepVarName,'
    echo '                      note this TBranch must be in a TTree found in tree_names.keys() of anaInfo.py'
    kill -INT $$;
}

# Check inputs
if [ -z ${3+x} ] || [ -z ${2+x} ] || [ -z ${1+x} ]
then
    usage
fi

# Make plots
INFILE=$1
ANATYPE=$2
BRANCHNAME=$3
for chan in {0..127}
do
    if [ $chan -eq 0 ]; then
        echo gemPlotter.py -i$INFILE -s$chan -a --anaType=$ANATYPE --branchName=$BRANCHNAME --rootOpt=RECREATE
        gemPlotter.py -i$INFILE -s$chan -a --anaType=$ANATYPE --branchName=$BRANCHNAME --rootOpt=RECREATE
    else
        echo gemPlotter.py -i$INFILE -s$chan -a --anaType=$ANATYPE --branchName=$BRANCHNAME --rootOpt=UPDATE
        gemPlotter.py -i$INFILE -s$chan -a --anaType=$ANATYPE --branchName=$BRANCHNAME --rootOpt=UPDATE
    fi
done
