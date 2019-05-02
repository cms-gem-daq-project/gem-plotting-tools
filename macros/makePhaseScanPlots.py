#!/bin/env python

r"""
``makePhaseScanPlots.py`` --- Plot results of GBT phase scans
===============================================================

Synopsis
--------

**makePhaseScanPlots.py** [*OPTIONS*] <*INPUT FILE*>

Description
-----------

The :program:`makePhaseScanPlots.py` tool is for plotting GBT phase scan results taken on one or more optohybrids on a AMC. This will create a 4-by-3 grid plot showing the phase scan results per OH on the AMC and in green the phase set points chosen will be shown on top of this 2D plot.


Mandatory Arguments
-------------------

The following list shows the mandatory inputs that must be supplied to execute
the script.

.. program:: makePhaseScanPlots.py

.. option:: [INPUT FILE]

    This is a delimited file, delimited by :token:`--delim`, whose first line is treated as a column header with subsequent lines listing detector name and scandate of the GBT phase scan.  For example:

        chamberName,scandate
        GE11-X-S-BARI-0008,2019.04.17.15.43
        GE11-X-S-BARI-0013,2019.04.17.16.34
        GE11-X-S-INDIA-0014,2019.04.18.18.06
    
    in the above example :token:`--delim` would be the comma ',' character

Optional Arguments
------------------

.. option:: --delim <DELIMITER>

    Delimiter in the mandatory input file. Default delimiter is the tab character `\t`

.. option:: --noSavedPlots

    If provided output plots will not be written to disk as `*.png` and `*.pdf` files.

.. option:: --outFile

    Name of output TFile that plots will be stored in

Examples
--------

To make a set of output plots, save them to disk as `*.png` and `*.pdf` files and also in a `TFile` call:

    makePhaseScanPlots.py listOfGBTPhaseScans.txt

To make a set of output plots, save them to disk as `*.png` and `*.pdf` files and also in a `TFile` call:

    makePhaseScanPlots.py listOfGBTPhaseScans.txt

To not write output `*.png` and `*.pdf` files call:

    makePhaseScanPlots.py --noSavedPlots listOfGBTPhaseScans.txt

To change the default delimiter to a different character call:

    makePhaseScanPlots.py --delim=',' listOfGBTPhaseScans.txt

"""

if __name__ == '__main__':
    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to makePhaseScanPlots.py')

    parser.add_argument("infilename",type=str,help="Name of input list of scan dates file in two column format")
    parser.add_argument("--delim",type=str,help="Delimiter used in infilename, default is tab character",default="\t")
    parser.add_argument("--noSavedPlots",action="store_true",help="If provided then output png & pdf files will not be made")
    parser.add_argument("--outFile",type=str,help="Name of output TFile to be produced",default="phaseScanResults.root")
    args = parser.parse_args()

    # Parse input file
    from gempython.gemplotting.utils.anautilities import getPhaseScanPlots, parseListOfScanDatesFile
    phaseTuple = parseListOfScanDatesFile(args.infilename, delim=args.delim)[0]

    # Check Paths
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')
    
    import os
    dataPath  = os.getenv('DATA_PATH')

    # Make Phase Scan Plots
    import ROOT as r
    outF = r.TFile(args.outFile,"RECREATE")
    for scan in phaseTuple:
        cName   = scan[0]
        scandate= scan[1]
        phaseScanFile = "{0}/{1}/gbtPhaseScan_{1}_{2}.log".format(dataPath,cName,scandate)
        phaseSetPtsFile = "{0}/{1}/gbtPhaseSetPoints_{1}_{2}.log".format(dataPath,cName,scandate)

        tupleDict = getPhaseScanPlots(
                    phaseScanFile, 
                    phaseSetPtsFile, 
                    identifier="{0}_{1}".format(cName,scandate),
                    savePlots=(not args.noSavedPlots)
                )
        dict_phaseScanDists = tupleDict[0]
        dict_phaseSetPtDists= tupleDict[1]

        outF.mkdir(cName)
        thisDir = outF.GetDirectory(cName)
        thisDir.cd()
        for ohN,plot in dict_phaseScanDists.iteritems():
            plot.Write()
        for ohN,plot in dict_phaseSetPtDists.iteritems():
            plot.Write()
            pass
        pass
    
    print("Goodbye")
