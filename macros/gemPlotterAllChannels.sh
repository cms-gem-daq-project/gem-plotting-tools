#!/bin/bash
# Usage:
# ./gemPlotterAllChannels.sh <InFile> <anaType> <branchName>

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
