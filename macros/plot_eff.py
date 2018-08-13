#!/bin/env python

r"""
``plot_eff.py`` --- Perform an efficiency analysis
==================================================

Synopsis
--------

**plot_eff.py** :token:`--latSig` <*LATENCY BIN*> :token:`-i` <*INPUT FILE*> :token:`-v` <*VFAT*> [*OPTIONS*]

Description
-----------

For some test stands where you have configured the input L1A to pass only
through a specific point of a detector you can use the data taken by
:program:`ultraLatency.py` to calculate the efficiency of the detector. To help
you perform this analysis the :program:`plot_eff.py` tool has been created.

Arguments
---------

Mandatory arguments
...................

The following list shows the mandatory inputs that must be supplied to execute
the script:

.. program:: plot_eff.py

.. option:: --latSig <LATENCY BIN>

    Latency bin for which efficiency should be determined from.

.. option:: -i, --infilename <FILE>

    Physical filename of the input file to be passed to :program:`plot_eff.py`.
    The format of this input file should follow the :doc:`Three Column Format
    </scandate-list-formats>`.

.. option:: -v, --vfat <VFAT>

    Specify VFAT to use when calculating the efficiency.

Optional arguments
..................

The following list shows the optional inputs that can be supplied when
executing the script:

.. option::  --bkgSub

    Background subtraction is used to determine the efficiency instead of a
    single latency bin. May be used instead of the :token:`--latSig` option.

.. option:: -p, --print

    Prints a comma-separated table of the plot's data to the terminal. The
    format of this table will be compatible with the
    :program:`genericPlotter.py` executable of the `CMS GEM Analysis Framework
    <https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#3b-genericplotter>`_.

.. option:: --vfatList <COMMA SEPARATED LIST OF INT'S>

    List of VFATs to use when calculating the efficiency. May be used instead of
    the :token:`--vfat` option.

Note if the :option:`--bkgSub` option is used then you **must** first call
:program:`anaUltraLatency.py` for each of the scandates given in the
:option:`--infilename`.

Example
-------

To calculate the efficiency using VFATs 12 & 13 in latency bin 39 for a list of
scandates defined in ``listOfScanDates.txt`` call:

.. code-block:: bash

    plot_eff.py --infilename=listOfScanDates.txt --vfatList=12,13 --latSig=39 --print

To calculate the efficiency using VFAT4 using background subtraction first call
:program:`anaUltraLatency.py` on each of the scandates given in
``listOfScanDates.txt`` and then call:

.. code-block:: bash

    plot_eff.py --infilename=listOfScanDates.txt -v4 --bkgSub --print

Here --infilename should be a tab delimited file the first row of this file
should be column headings, the subsequent rows of this file should be data
lines. Example::

    ChamberName scandate    EffGain
    GEMINIm27L1 2017.08.29.18.11    5000
    GEMINIm27L1 2017.08.29.18.19    7500
    GEMINIm27L1 2017.08.29.18.33    10000
    GEMINIm27L1 2017.08.29.18.06    15000
    GEMINIm27L1 2017.08.30.08.22    20000

Then this will make a plot of Eff vs. EffGain from the data supplied

Internals
---------
"""

def calcEffErr(eff, nTriggers):
    """
    Returns the binomial error on the input efficiency

    Arguments:
        eff(float): Input efficency value (from 0.0 to 1.0)

        nTriggers(int): The number of triggers used when obtaining eff
    """

    import math
    return math.sqrt( (eff * ( 1. - eff) ) / nTriggers )

def calcEff(cName, scandate, vfatList, latBin, bkgSub=False):
    """
    Returns a tuple of (eff, sigma_eff)
    
    Arguments:
        cName(str): Chamber name, i.e. the value of a given key of the
            :py:data:`chamber_config
            <gempython.gemplotting.mapping.chamberInfo.chamber_config>` dict

        scandate(str): Scandate of the :program:`ultraLatency.py` measurement

        vfatList(list of int): List of vfats to use for calculating the
            efficiency

        latBin(int): Latency bin to determine the eff for

        bkgSub(bool): Perform background subtraction
    """
    
    from gempython.gemplotting.utils.anautilities import getDirByAnaType

    import os

    # Setup paths
    dirPath = "%s/%s"%(getDirByAnaType("latency",cName), scandate)
    filename_RAW = dirPath + "/LatencyScanData.root"
    filename_ANA = dirPath + "/LatencyScanData/latencyAna.root"

    # Load data - RAW
    import root_numpy as rp
    import numpy as np
    list_bNames = ["vfatN","latency","Nhits","Nev"]
    try:
        array_VFATData = rp.root2array(filename_RAW,"latTree",list_bNames)
        pass
    except Exception as e:
        print '%s does not seem to exist'%filename_RAW
        print e
        exit(os.EX_NOINPUT)

    # Load data - ANA
    import ROOT as r
    try:
        anaFile = r.TFile(filename_ANA,"READ")
    except Exception as e:
        print '%s does not seem to exist'%filename_ANA
        print e
        exit(os.EX_NOINPUT)

    # Determine hits and triggers
    nTriggers = np.asscalar(np.unique(array_VFATData['Nev']))
    nHits = 0.0
    for vfat in vfatList:
        if bkgSub:
            try:
                gSignalNoBkg = anaFile.Get("grVFATNSignalNoBkg")
                vfatHits = r.Double()
                vfatPos = r.Double()
                gSignalNoBkg.GetPoint(vfat,vfatPos,vfatHits)
                nHits += vfatHits
            except Exception as e:
                print "grVFATNSignalNoBkg not present in TFile %s"%filename_ANA
                print "Maybe you forgot to analyze with the --fit, --latSigRange, and --latNoiseRange options?"
                print e
                exit(os.EX_DATAERR)
        else:
            vfatData = array_VFATData[ array_VFATData['vfatN'] == vfat]
            latData = vfatData[vfatData['latency'] == latBin]
            nHits += np.asscalar(latData['Nhits'])

    # Calc Eff & Error
    return (nHits / nTriggers, calcEffErr(nHits / nTriggers, nTriggers) )

if __name__ == '__main__':
    from gempython.gemplotting.utils.anautilities import parseListOfScanDatesFile
    from gempython.utils.wrappers import envCheck
    from gempython.gemplotting.macros.plotoptions import parser
    from gempython.gemplotting.mapping.chamberInfo import chamber_config, GEBtype
    
    import os
    
    parser.add_option("--bkgSub", action="store_true", dest="bkgSub",
                      help="Use Background Subtracted info from fit analysis in anaUltraLatency.py", metavar="bkgSub")
    parser.add_option("--latSig", type="int", dest="latSig", default=None,
                      help="Latency bin where signal is found", metavar="latSig")
    parser.add_option("-p","--print", action="store_true", dest="printData",
                      help="Prints a comma separated table with the data to the terminal", metavar="printData")
    parser.add_option("--vfatList", type="string", dest="vfatList", default=None,
                      help="Comma separated list of VFATs to consider, e.g. '12,13'", metavar="vfatList")

    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()
    
    # Check Paths
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath  = os.getenv('ELOG_PATH')

    # Get VFAT List
    list_VFATs = []
    if options.vfatList != None:
        list_VFATs = map(int, options.vfatList.split(','))
    elif options.vfat != None:
        list_VFATs.append(options.vfat)
    else:
        print "You must specify at least one VFAT to be considered"
        exit(os.EX_USAGE)

    # Check that the user supplied a latency value
    if options.latSig is None and not options.bkgSub:
        print "You must specify the latency bin of the signal peak (--latSig) or ask for background subtracted analysis (--bkgSub)"
        exit(os.EX_USAGE)
    
    # Get info from input file
    parsedTuple = parseListOfScanDatesFile(options.filename)
    parsedAnalysisList = parsedTuple[0]
    strIndepVar = parsedTuple[1]

    # Loop Over inputs
    list_EffData = []
    strChamberName = ""
    for analysisTuple in parsedAnalysisList:
        if len(strChamberName) == 0:
            strChamberName = analysisTuple[0]
        
        tuple_eff = calcEff(analysisTuple[0], analysisTuple[1], list_VFATs, options.latSig, options.bkgSub)
        list_EffData.append((float(analysisTuple[2]), tuple_eff[0], tuple_eff[1]))

    # Print to the user
    # Using format compatible with: https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data
    if options.printData:
        print ""
        print "[BEGIN_DATA]"
        print "\tVAR_INDEP,VAR_DEP,VAR_DEP_ERR"
        for dataPt in list_EffData:
            print "\t%f,%f,%f"%(dataPt[0],dataPt[1],dataPt[2])
        print "[END_DATA]"
        print ""

    # Plot the efficiency plot
    import ROOT as r
    r.gROOT.SetBatch(True)
    grEffPlot = r.TGraphErrors(len(list_EffData))
    grEffPlot.SetTitle("Eff from VFATs: [%s]"%(options.vfatList))
    grEffPlot.SetMarkerStyle(20)
    grEffPlot.SetLineWidth(2)
    for idx in range(len(list_EffData)):
        grEffPlot.SetPoint(idx, list_EffData[idx][0], list_EffData[idx][1])
        grEffPlot.SetPointError(idx, 0., list_EffData[idx][2])

    # Draw this plot on a canvas
    from gempython.gemplotting.utils.anautilities import getStringNoSpecials
    strIndepVarNoBraces = getStringNoSpecials(strIndepVar).replace('_','')
    canvEff = r.TCanvas("%s_Eff_vs_%s"%(strChamberName,strIndepVarNoBraces),"%s: Eff vs. %s"%(strChamberName,strIndepVarNoBraces),600,600)
    canvEff.cd()
    grEffPlot.Draw("APE1")
    grEffPlot.GetXaxis().SetTitle(strIndepVar)
    grEffPlot.GetYaxis().SetDecimals(True)
    grEffPlot.GetYaxis().SetRangeUser(0.0,1.0)
    grEffPlot.GetYaxis().SetTitle("Efficiency")
    grEffPlot.GetYaxis().SetTitleOffset(1.2)
    canvEff.Update()
    strCanvName = elogPath + "/%s_Eff_vs_%s.png"%(strChamberName,strIndepVarNoBraces)
    canvEff.SaveAs(strCanvName)
    
    print ""
    print "To view your plot, execute:"
    print ("eog " + strCanvName)
    print ""

    # Make an output ROOT file
    strRootName = elogPath + "/%s_Eff_vs_%s.root"%(strChamberName,strIndepVarNoBraces)
    outF = r.TFile(strRootName,"recreate")
    grEffPlot.Write()
    canvEff.Write()
    
    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
