#!/bin/env python

r"""
``anaSBitThresh`` -- analyzes SBIT Rate Scan Data vs. CFG_THR_ARM_DAC
=============

Synopsis
--------

**anaSBitThresh.py** [*OPTIONS*] [input file]

Description
-----------

This script reads in a TFile which should hold a TTree called "rateTree" which is an instance of the ``gemSbitRateTreeStructure`` class from ``gempython.vfatqc.utils.treeStructure``.  This will use the ``chamber_config`` info found in `gempython.gemplotting.mapping.chamberInfo`` to determine which (shelf,slot,link) info stored in the TTree corresponds to which detector.

For each unqiue (shelf,slot,link) triplet in the input file the script will analyze the stored data and produce either 1D or 2D plots depending on if the data was taken with the OR of all channels or by channel number (determined automatically by the algorithm) and it will calculate when the SBIT rate goes to zero as a function of the CFG_THR_ARM_DAC.

It will place a TFile containing output TGraphError objects in the ``$DATA_PATH/ChamberName/sbitRate/perchannel(channelOR)/scandate`` directory for measrements per channel (taking OR of all channels).

Additionally for each (shelf,slot,link) triplet in the input file it will produce a vfatConfig.txt file (in the same directory mentioned above) that will be compatible with TTree::ReadFile() method.  The format of which looks like:

    vfatN/I:vt1/I:trimRange/I
    0       44      0
    1       22      0
    ...
    ...
    22      12      0
    23      76      0

This can be used with the ``configure(...)`` function from ``gempython.vfatqc.utils.confUtils`` to configure the ``CFG_THR_ARM_DAC`` register on a detectors VFATs.

Arguments
---------

.. program:: anaSBitThresh.py

.. option:: infilename

    Name of the input TFile containing a TTree called ``rateTree`` which is an instance of the ``gemSbitRateTreeStructure`` from ``gempython.vfatqc.utils.treeStructure``.

.. option:: -d, --debug

    Debugging flag, if provided prints additional information to terminal

.. option:: -o, --outfilename

    Name of output TFile to be created, defaults to ``SBitRatePlots.root``

.. option:: -m, --maxNoiseRate

    Rate provided in Hertz to define the cut off rate.  One the SBIT Rate reaches below this number the ``CFG_THR_ARM_DAC`` when this occurs will be stored and in the output ``vfatConfig.txt`` file.

Example
-------

.. code-block:: bash

    anaSBitThresh --maxNoiseRate=0.0 /path/to/input.root

"""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to anaDACScan.py')
    parser.add_argument("infilename", type=str, help="Filename from which input data is contained, expected to have a TTree called 'rateTree' with branches defined by the gemSbitRateTreeStructure class")
    parser.add_argument('-d','--debug', action='store_true', help="Prints additional debugging information")
    parser.add_argument('-o','--outfilename', type=str, default="SBitRatePlots.root", help="Filename to which analyzed data is written")
    parser.add_argument("-m","--maxNoiseRate", type=float, dest="maxNoiseRate", default=0,
                    help="Max Noise Rate allowed in Hz")
    args = parser.parse_args()

    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")
    envCheck("ELOG_PATH")

    import os
    elogPath = os.getenv("ELOG_PATH")

    # load input file
    import ROOT as r
    sbitThreshFile = r.TFile(args.infilename,"READ")

    # determine scandate
    if len(args.infilename.split('/')) > 1 and len(args.infilename.split('/')[len(args.infilename.split('/')) - 2].split('.')) == 5:
        scandate = args.infilename.split('/')[len(args.infilename.split('/')) - 2]
    else:    
        scandate = 'noscandate'

    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    from gempython.gemplotting.utils.anautilities import getDirByAnaType, sbitRateAnalysis
    anaResults = sbitRateAnalysis(
            chamber_config = chamber_config, 
            rateTree = sbitThreshFile.rateTree,
            cutOffRate = args.maxNoiseRate,
            debug = args.debug,
            outfilename = args.outfilename,
            scandate = scandate)

    perchannel = anaResults[0]
    dict_dacValsBelowCutOff = anaResults[1]

    from gempython.utils.gemlogger import printGreen
    for ohKey,innerDictByVFATKey in dict_dacValsBelowCutOff["THR_ARM_DAC"].iteritems():
        if scandate == 'noscandate':
            vfatConfg = open("{0}/{1}/vfatConfig.txt".format(elogPath,chamber_config[ohKey]),'w')
            printGreen("Output Data for {0} can be found in:\n\t\{1}/{0}\n".format(chamber_config[ohKey],elogPath))
        else:
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", chamber_config[ohKey])
            else:
                strDirName = getDirByAnaType("sbitRateor", chamber_config[ohKey])
                pass
            vfatConfg = open("{0}/{1}/vfatConfig.txt".format(strDirName,scandate),'w')
            printGreen("Output Data for {0} can be found in:\n\t\{1}/{2}\n".format(chamber_config[ohKey],strDirName,scandate))
            pass

        vfatConfg.write("vfatN/I:vt1/I:trimRange/I\n")
        for vfat,armDACVal in innerDictByVFATKey.iteritems():
            vfatConfg.write('%i\t%i\t%i\n'%(vfat, armDACVal,0))
            pass
        vfatConfg.close()
        pass

    print('Analysis Completed Successfully')
