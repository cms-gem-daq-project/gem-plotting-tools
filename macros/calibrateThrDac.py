#!/bin/env python

r"""
``calibrateThrDac.py`` --- Calibrating CFG_THR_*_DAC of VFAT3
====================

Synopsis
--------

**calibrateThrDac.py** :token:`--fitRange` <*FIT RANGE*> :token:`--listOfVFATs` <*LIST OF VFATS INPUT FILE*> :token:`--noLeg` :token:`--savePlots` :token:[*FILENAME*]

Description
-----------

The :program:`calibrateThrDac.py` tool is for calibrating either the ``CFG_THR_ARM_DAC`` or the ``CFG_THR_ZCC_DAC`` register of a set of ``vfat3`` ``ASIC``s.  The user should have taken a set of scurves at varying ``CFG_THR_X_DAC`` settings, for ``X={ARM,ZCC}``. Then these scurves are expected to have been analyzed, including fitting, with the :program:`anaUltraScurve.py`.  The correct `CFG_CAL_DAC` calibration must have been used during this analysis.

The ``FILENAME`` file is expected to be in the :any:`Three Column Format` with the independent variable being ``CFG_THR_X_DAC``. For each scandate in ``FILENAME`` the scruve ``gScurveMeanDist_*`` and ``gScurveSigmaDist_*`` ``TGraphErrors`` objects for each VFAT, and summary level, will be fit with a Gaussian distribution.  The mean of this Gaussian will be plotted against the provided ``CFG_THR_X_DAC`` value with the Gaussian's sigma taken as the error on the mean.  The resulting scurveMean(Sigma) vs. ``CFG_THR_X_DAC`` distribution will be fit with a ``pol1``(``pol0``) function.  The fit function for the scurveMean vs. ``CFG_THR_X_DAC`` gives the calibration of the THR DAC in terms of fC while the fit function for the scurveSigma vs. ``CFG_THR_X_DAC`` gives the horizontal asymptote of the average ENC across the ``vfat``.

An output table will be produced at the end of the function call which shows the calibration information and ENC by VFAT position and overall (e.g. vfat position = ``All``).  Numerically the ``All`` case is assigned a value of ``-1``.

Output files will be found in :envvar:`$ELOG\_PATH`.  The ``calFile_CFG_THR_X_DAC_<Det S/N>.txt`` file will be a text file specifying the ``CFG_THR_X_DAC`` calibration parameters (slope and intercept) by vfat position.  Additionally all ``TObject``s created during the analysis will be found in ``calFile_<Det S/N>_CFG_THR_X_DAC.root``.

Mandatory arguments
-------------------

.. option:: [*FILENAME*]

    Physical filename of the input file to be passed to
    :program:`calibrateThrDac.py`.  See :any:`Three Column Format` for
    details on the format and contents of this file.  The independent
    variable is expected to be ``CFG_THR_X_DAC`` for ``X={ARM,ZCC}``.

Optional arguments
------------------

.. option:: --fitRange <FIT RANGE>

    Two comma separated integers which specify the range
    of 'CFG_THR_*_DAC' to use in fitting when deriving the
    calibration curve.

.. option:: --listOfVFATs <LIST OF VFATS INPUT FILE>

    If provided the VFATID will be taken from this file
    rather than scurveTree. Tab delimited file, first line
    is a column header, subsequent lines specify
    respectively VFAT position and VFAT serial number.
    Lines beginning with the '#' character will be skipped.

.. option:: --noLeg

    Do not draw a TLegend on the output plots

.. option:: --savePlots

    Make ``*.png`` file for all plots that will be saved in
    the output TFile

Example
-------

To use the scurve fit results from scandates contained in listOfScanDates_armCal.txt execute:

.. code-block:: bash

    calibrateThrDac.py listOfScanDates_armCal.txt --fitRange=30,150

Environment
-----------

.. glossary::

    :envvar:`DATA_PATH`
        The location of input data

    :envvar:`ELOG_PATH`
        Results are written in the directory pointed to by this variable

Internals
---------
"""

if __name__ == '__main__':
    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to calibrateThrDac.py')
    parser.add_argument("filename", type=str, 
            help="Tab delimited file specifying the input list of scandates, in three column format, specifying chamberName, scandate, and either CFG_THR_ARM_DAC or CFG_THR_ZCC_DAC value", 
            metavar="filename")

    parser.add_argument("--fitRange", type=str, dest="fitRange", default="0,255", 
            help="Two comma separated integers which specify the range of 'CFG_THR_*_DAC' to use in fitting when deriving the calibration curve",
            metavar="fitRange") 
    parser.add_argument("--listOfVFATs", type=str, dest="listOfVFATs", default=None,
            help="If provided the VFATID will be taken from this file rather than scurveTree.  Tab delimited file, first line is a column header, subsequent lines specify respectively VFAT position and VFAT serial number.  Lines beginning with the '#' character will be skipped", 
            metavar="listOfVFATs")
    parser.add_argument("--noLeg", action="store_true", dest="noLeg",
            help="Do not draw a TLegend on the output plots")
    parser.add_argument("--savePlots", action="store_true", dest="savePlots",
            help="Make *.png file for all plots that will be saved in the output TFile")
    args = parser.parse_args()

    # Suppress all pop-ups from ROOT
    import ROOT as r
    r.gROOT.SetBatch(True)

    # Check Paths
    import os
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath = os.getenv('ELOG_PATH')

    # Get info from input file
    from gempython.gemplotting.utils.anautilities import getCyclicColor, getDirByAnaType, filePathExists, make3x8Canvas, parseListOfScanDatesFile
    parsedTuple = parseListOfScanDatesFile(args.filename)
    listChamberAndScanDate = parsedTuple[0]
    thrDacName = parsedTuple[1]
    chamberName = listChamberAndScanDate[0][0]

    # Do we load an optional vfat serial number table? (e.g. chips did not have serial number in efuse burned in)
    import numpy as np
    import root_numpy as rp
    if args.listOfVFATs is not None:
        try:
            mapVFATPos2VFATSN = np.loadtxt(
                        fname = args.listOfVFATs,
                        dtype={'names':('vfatN', 'serialNum'),
                                'formats':('u4', 'u4')},
                        skiprows=1,
                    )
        except Exception as e:
            print '{0} does not seem to exist, is not readable, or does not have the right format'.format(args.listOfVFATs)
            print e
            exit(os.EX_NOINPUT)
            pass
    else:
        mapVFATPos2VFATSN = np.zeros(24,dtype={'names':('vfatN', 'serialNum'),'formats':('u4', 'u4')})

    # Get list of THR DAC values
    listOfThrValues = []
    for infoTuple in listChamberAndScanDate:
        listOfThrValues.append(infoTuple[2])
    listOfThrValues.sort()

    # Determine step size in THR DAC values
    # This is for making box plots
    deltaBins = np.diff(listOfThrValues)
    uniqueDeltas = np.unique(deltaBins)
    if len(uniqueDeltas) == 1:
        stepSize = np.unique(deltaBins)
        binMin = min(listOfThrValues)-stepSize*0.5
        binMax = max(listOfThrValues)+stepSize*0.5
        nBins = len(listOfThrValues)
    #else:
    #    from array import array
    #    binEdges = []
    #    for idx,val in enumerate(listOfThrValues):
    #        if( idx < (len(listOfThrValues)-1)):
    #            binEdges.append(val - 0.5*deltaBins[idx])
    #        else:
    #            binEdges.append(val - 0.5*deltaBins[idx-1])
    #            binEdges.append(val + 0.5*deltaBins[idx-1])
    #    binEdges = array('d',binEdges)
    #    nBins = len(binEdges)-1
    
    # Make containers
    # In each case where vfat position is used as a key, the value of -1 is the sum over the entire detector
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_gScurveMean = ndict() #Stores TGraphErrors objects. Outer key is CFG_THR_*_DAC value; Inner key follows vfat position
    dict_gScurveSigma = ndict()
    dict_funcScurveMean = ndict()
    dict_funcScurveSigma = ndict()

    dict_mGraphScurveMean = {} # Key is VFAT position, stores the dict_gScurveMean[*][vfat] for a given vfat
    dict_mGraphScurveSigma = {}
    dict_ScurveMeanVsThrDac = {} # Key is VFAT position
    dict_ScurveMeanVsThrDac_BoxPlot = {} # Key is VFAT position
    dict_ScurveSigmaVsThrDac = {}
    dict_ScurveSigmaVsThrDac_BoxPlot = {}

    legArmDacValues = r.TLegend(0.5,0.5,0.9,0.9)

    # Get the plots from all files
    from gempython.gemplotting.utils.anaInfo import tree_names
    for idx,infoTuple in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType("scurve", infoTuple[0])
        if not filePathExists(dirPath, infoTuple[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, infoTuple[1])
            print 'Please cross-check, exiting!'
            outF.Close()
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, infoTuple[1], tree_names["scurveAna"][0])

        # Load the file
        r.TH1.AddDirectory(False)
        scanFile   = r.TFile(filename,"READ")

        if scanFile.IsZombie():
            print("{0} is a zombie!!!".format(filename))
            print("Please double check your input list of scandates: {0}".format(args.filename))
            print("And then call this script again")
            raise IOError

        # Determine vfatID
        list_bNames = ['vfatN','vfatID']
        array_vfatData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)
        array_vfatData = np.unique(array_vfatData)
        
        # Get scurve data for this arm dac value (used for boxplots)
        list_bNames = ['noise', 'threshold', 'vfatN', 'vthr']
        scurveFitData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)

        ###################
        # Get and fit individual distributions
        ###################
        for vfat in range(-1,24):
            if vfat == -1:
                suffix = "All"
                loadPath = suffix
                directory = "Summary"
            else:
                if args.listOfVFATs is not None:
                    vfatID = mapVFATPos2VFATSN[mapVFATPos2VFATSN['vfatN'] == vfat]
                else:
                    if len(array_vfatData[array_vfatData['vfatN'] == vfat]) > 0:
                        mapVFATPos2VFATSN[vfat]['vfatN'] = vfat
                        mapVFATPos2VFATSN[vfat]['serialNum'] = array_vfatData[array_vfatData['vfatN'] == vfat]['vfatID']
                    else:
                        mapVFATPos2VFATSN[vfat]['vfatN'] = vfat
                        mapVFATPos2VFATSN[vfat]['serialNum'] = 0
                suffix = "vfatN{0}_vfatID{1}".format(vfat,mapVFATPos2VFATSN[vfat]['serialNum'])
                loadPath = "vfat{0}".format(vfat)
                directory = loadPath.upper()

            # Make the TMultiGraph Objects
            if idx == 0:
                # Scurve Mean
                dict_mGraphScurveMean[vfat] = r.TMultiGraph("mGraph_ScurveMeanByThrDac_{0}".format(suffix),suffix)

                dict_ScurveMeanVsThrDac[vfat] = r.TGraphErrors(len(listChamberAndScanDate))
                dict_ScurveMeanVsThrDac[vfat].SetTitle(suffix)
                dict_ScurveMeanVsThrDac[vfat].SetName("gScurveMean_vs_{0}_{1}".format(thrDacName,suffix))
                dict_ScurveMeanVsThrDac[vfat].SetMarkerStyle(23)
                
                if len(uniqueDeltas) == 1:
                    #placeholder
                    dict_ScurveMeanVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveMean_vs_{0}_{1}".format(thrDacName,suffix),suffix,nBins,binMin,binMax,1002,-0.1,100.1)
                else:
                    #dict_ScurveMeanVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveMean_vs_{0}_{1}".format(thrDacName,suffix),suffix,nBins,binEdges,1002,-0.1,100.1)
                    dict_ScurveMeanVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveMean_vs_{0}_{1}".format(thrDacName,suffix),suffix,256,-0.5,255.5,1002,-0.1,100.1)
                dict_ScurveMeanVsThrDac_BoxPlot[vfat].SetXTitle(thrDacName)
                dict_ScurveMeanVsThrDac_BoxPlot[vfat].SetYTitle("Scurve Mean #left(fC#right)")

                # Scurve Sigma
                dict_mGraphScurveSigma[vfat] = r.TMultiGraph("mGraph_ScurveSigmaByThrDac_{0}".format(suffix),suffix)

                dict_ScurveSigmaVsThrDac[vfat] = r.TGraphErrors(len(listChamberAndScanDate))
                dict_ScurveSigmaVsThrDac[vfat].SetTitle(suffix)
                dict_ScurveSigmaVsThrDac[vfat].SetName("gScurveSigma_vs_{0}_{1}".format(thrDacName,suffix))
                dict_ScurveSigmaVsThrDac[vfat].SetMarkerStyle(23)
                
                if len(uniqueDeltas) == 1:
                    #placeholder
                    dict_ScurveSigmaVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveSigma_vs_{0}_{1}".format(thrDacName,suffix),suffix,nBins,binMin,binMax,504,-0.1,25.1)
                else:
                    #dict_ScurveSigmaVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveSigma_vs_{0}_{1}".format(thrDacName,suffix),suffix,nBins,binEdges,504,-0.1,25.1)
                    dict_ScurveSigmaVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveSigma_vs_{0}_{1}".format(thrDacName,suffix),suffix,256,-0.5,255.5,504,-0.1,25.1)
                dict_ScurveSigmaVsThrDac_BoxPlot[vfat].SetXTitle(thrDacName)
                dict_ScurveSigmaVsThrDac_BoxPlot[vfat].SetYTitle("Scurve Sigma #left(fC#right)")

            ###################
            ### Scurve Mean ###
            ###################
            dict_gScurveMean[infoTuple[2]][vfat] = scanFile.Get("{0}/gScurveMeanDist_{1}".format(directory,loadPath))
            if vfat > -1:
                dict_gScurveMean[infoTuple[2]][vfat].SetName("gScurveMeanDist_{0}_thrDAC{1}".format(suffix,infoTuple[2]))
            else:
                dict_gScurveMean[infoTuple[2]][vfat].SetName("{0}_thrDAC{1}".format(dict_gScurveMean[infoTuple[2]][vfat].GetName(),infoTuple[2]))

            #Set style of TGraphErrors
            dict_gScurveMean[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerStyle(21)
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Declare the fit function
            arrayX = np.array(dict_gScurveMean[infoTuple[2]][vfat].GetX())
            dict_funcScurveMean[infoTuple[2]][vfat] = r.TF1(
                    "func_{0}".format((dict_gScurveMean[infoTuple[2]][vfat].GetName()).strip('g')),
                    "gaus",
                    np.min(arrayX),
                    np.max(arrayX))

            # Set style of TF1
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineWidth(2)
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineStyle(3)
            dict_funcScurveMean[infoTuple[2]][vfat].SetParLimits(1,0,100) #Limit mean position to be physical

            # Fit
            dict_gScurveMean[infoTuple[2]][vfat].Fit(dict_funcScurveMean[infoTuple[2]][vfat],"QR")

            # Add to MultiGraph
            dict_mGraphScurveMean[vfat].Add(dict_gScurveMean[infoTuple[2]][vfat])

            # Add point to calibration curve
            dict_ScurveMeanVsThrDac[vfat].SetPoint(
                    idx,
                    infoTuple[2],
                    dict_funcScurveMean[infoTuple[2]][vfat].GetParameter("Mean"))
            dict_ScurveMeanVsThrDac[vfat].SetPointError(
                    idx,
                    0,
                    dict_funcScurveMean[infoTuple[2]][vfat].GetParameter("Sigma"))

            ###################
            ### Scurve Sigma ##
            ###################
            dict_gScurveSigma[infoTuple[2]][vfat] = scanFile.Get("{0}/gScurveSigmaDist_{1}".format(directory,loadPath))
            if vfat > -1:
                dict_gScurveSigma[infoTuple[2]][vfat].SetName("gScurveSigmaDist_{0}_thrDAC{1}".format(suffix,infoTuple[2]))
            else:
                dict_gScurveSigma[infoTuple[2]][vfat].SetName("{0}_thrDAC{1}".format(dict_gScurveSigma[infoTuple[2]][vfat].GetName(),infoTuple[2]))

            #Set style of TGraphErrors
            dict_gScurveSigma[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerStyle(21)
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Get the fitted function
            arrayX = np.array(dict_gScurveSigma[infoTuple[2]][vfat].GetX())
            dict_funcScurveSigma[infoTuple[2]][vfat] = r.TF1(
                    "func_{0}".format((dict_gScurveSigma[infoTuple[2]][vfat].GetName()).strip('g')),
                    "gaus",
                    np.min(arrayX),
                    np.max(arrayX))

            # Set style of TF1
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineWidth(2)
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineStyle(3)

            # Fit
            dict_gScurveSigma[infoTuple[2]][vfat].Fit(dict_funcScurveSigma[infoTuple[2]][vfat],"QR")

            # Add to MultiGraph
            dict_mGraphScurveSigma[vfat].Add(dict_gScurveSigma[infoTuple[2]][vfat])

            # Add point to calibration curve
            dict_ScurveSigmaVsThrDac[vfat].SetPoint(
                    idx,
                    infoTuple[2],
                    dict_funcScurveSigma[infoTuple[2]][vfat].GetParameter("Mean"))
            dict_ScurveSigmaVsThrDac[vfat].SetPointError(
                    idx,
                    0,
                    dict_funcScurveSigma[infoTuple[2]][vfat].GetParameter("Sigma"))

            ###################
            # Make an entry in the TLegend
            ###################
            if vfat == 0:
                legArmDacValues.AddEntry(
                        dict_gScurveSigma[infoTuple[2]][vfat],
                        "{0} = {1}".format(thrDacName, infoTuple[2]),
                        "LPE")

        #####################
        ### Fill Box Plots ##
        #####################
        for idx in range(0,len(scurveFitData)):
            scurveMean = scurveFitData[idx]['threshold']
            scurveSigma = scurveFitData[idx]['noise']
            thrDacVal = scurveFitData[idx]['vthr']
            vfatN = scurveFitData[idx]['vfatN']

            # All VFATs
            dict_ScurveMeanVsThrDac_BoxPlot[-1].Fill(thrDacVal,scurveMean)
            dict_ScurveSigmaVsThrDac_BoxPlot[-1].Fill(thrDacVal,scurveSigma)

            # Per VFAT
            dict_ScurveMeanVsThrDac_BoxPlot[vfatN].Fill(thrDacVal,scurveMean)
            dict_ScurveSigmaVsThrDac_BoxPlot[vfatN].Fill(thrDacVal,scurveSigma)

    ###################
    # Make output calibration file
    ###################
    try:
        calThrDacFile = open("{0}/calFile_{2}_{1}.txt".format(elogPath,chamberName,thrDacName),'w')
    except IOError as e:
        print("Caught Exception: {0}".format(e))
        print("Unabled to open file '{0}/calFile_{2}_{1}.txt'".format(elogPath,chamberName,thrDacName))
        print("Perhaps the path does not exist or you do not have write permissions?")
        exit(os.EX_IOERR)
    calThrDacFile.write("vfatN/I:slope/F:intercept/F\n")

    ###################
    # Make output ROOT file
    ###################
    outFileName = "{0}/calFile_{2}_{1}.root".format(elogPath,chamberName,thrDacName)
    outFile = r.TFile(outFileName,"RECREATE")

    # Plot Containers
    dict_canvScurveMeanByThrDac = {}
    dict_canvScurveSigmaByThrDac = {}

    dict_canvScurveMeanVsThrDac = {}
    dict_canvScurveSigmaVsThrDac = {}

    dict_canvScurveMeanVsThrDac_BoxPlot = {}
    dict_canvScurveSigmaVsThrDac_BoxPlot = {}

    dict_funcScurveMeanVsThrDac = {}
    
    ###################
    # Now Make plots & Fit DAC Curves
    ###################
    print("| vfatN | cal_thr_m | cal_thr_m_err | cal_thr_b | cal_thr_b_err | noise | noise_err |")
    print("| :---: | :-------: | :-----------: | :-------: | :-----------: | :---: | :-------: |")
    fitRange = [int(item) for item in args.fitRange.split(",")]
    for vfat in range(-1,24):
        if vfat == -1:
            suffix = "All"
            directory = "Summary"
        else:
            suffix = "vfatN{0}_vfatID{1}".format(vfat,mapVFATPos2VFATSN[vfat]['serialNum'])
            directory = "VFAT{0}".format(vfat)

        thisDirectory = outFile.mkdir(directory)
        RawDataDir = thisDirectory.mkdir("RawData")
        RawDataDirMean = RawDataDir.mkdir("ScurveMean")
        RawDataDirSigma = RawDataDir.mkdir("ScurveSigma")
        for idx,infoTuple in enumerate(listChamberAndScanDate):
            RawDataDirMean.cd()
            dict_gScurveMean[infoTuple[2]][vfat].Write()
            RawDataDirSigma.cd()
            dict_gScurveSigma[infoTuple[2]][vfat].Write()
        thisDirectory.cd()

        # Mean by CFG_THR_*_DAC
        dict_canvScurveMeanByThrDac[vfat] = r.TCanvas("canvScurveMeanByThrDac_{0}".format(suffix),"Scurve Mean by THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanByThrDac[vfat].cd()
        dict_mGraphScurveMean[vfat].Draw("APE1")
        dict_mGraphScurveMean[vfat].GetXaxis().SetRangeUser(0,80)
        dict_mGraphScurveMean[vfat].GetXaxis().SetTitle("Scurve Mean #left(fC#right)")
        dict_mGraphScurveMean[vfat].Draw("APE1")
        dict_mGraphScurveMean[vfat].Write()

        # Sigma by CFG_THR_*_DAC
        dict_canvScurveSigmaByThrDac[vfat] = r.TCanvas("canvScurveSigmaByThrDac_{0}".format(suffix),"Scurve Sigma by THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaByThrDac[vfat].cd()
        dict_mGraphScurveSigma[vfat].Draw("APE1")
        dict_mGraphScurveSigma[vfat].GetXaxis().SetRangeUser(0,5)
        dict_mGraphScurveSigma[vfat].GetXaxis().SetTitle("Scurve Sigma #left(fC#right)")
        dict_mGraphScurveSigma[vfat].Draw("APE1")
        dict_mGraphScurveSigma[vfat].Write()

        thrDacIndexPairs = []
        for i in range(0,dict_ScurveMeanVsThrDac[vfat].GetN()):
            thrDacVal = r.Double()
            scurveMean = r.Double()
            dict_ScurveMeanVsThrDac[vfat].GetPoint(i,thrDacVal,scurveMean)
            thrDacIndexPairs.append([thrDacVal,i])

        thrDacIndexPairs.sort()    
        
        #remove THR DAC values where there appear to be pedestal effects
        tgraph_scurveSigmaHighThrDacVal=r.TGraphErrors(5)
        scurveSigmaMeanHighThrDacVal = 0
        for i in range(len(thrDacIndexPairs)-5,len(thrDacIndexPairs)):
            thrDacVal = r.Double()
            scurveSigma = r.Double()
            dict_ScurveSigmaVsThrDac[vfat].GetPoint(thrDacIndexPairs[i][1],thrDacVal,scurveSigma)
            scurveSigmaError = dict_ScurveSigmaVsThrDac[vfat].GetErrorY(thrDacIndexPairs[i][1])
            tgraph_scurveSigmaHighThrDacVal.SetPoint(i-(len(thrDacIndexPairs)-5),thrDacVal,scurveSigma)
            tgraph_scurveSigmaHighThrDacVal.SetPointError(i-(len(thrDacIndexPairs)-5),0,scurveSigmaError)

        tgraph_scurveSigmaHighThrDacVal.Fit("pol0","Q")    
        sigmaHighThrDacPlusError = tgraph_scurveSigmaHighThrDacVal.GetFunction("pol0").GetParameter(0)+tgraph_scurveSigmaHighThrDacVal.GetFunction("pol0").GetParError(0)
        sigmaHighThrDacChiSquaredOverNdof = tgraph_scurveSigmaHighThrDacVal.GetFunction("pol0").GetChisquare()/4.0

        tgraph_scurveMeanVsThrDacForFit = r.TGraphErrors()

        setLastUnremovedScurveMean = False
        for i in range(0,len(thrDacIndexPairs)):
            i = len(thrDacIndexPairs) - 1 - i
            thrDacVal = r.Double()
            scurveSigma = r.Double()
            scurveMean = r.Double()
            dict_ScurveSigmaVsThrDac[vfat].GetPoint(thrDacIndexPairs[i][1],thrDacVal,scurveSigma)
            dict_ScurveMeanVsThrDac[vfat].GetPoint(thrDacIndexPairs[i][1],thrDacVal,scurveMean)
            scurveSigmaError = dict_ScurveSigmaVsThrDac[vfat].GetErrorY(thrDacIndexPairs[i][1])
            scurveMeanError = dict_ScurveMeanVsThrDac[vfat].GetErrorY(thrDacIndexPairs[i][1])
            if scurveMean < 0.1:
                continue
            if not setLastUnremovedScurveMean:
                lastUnremovedScurveMean = scurveMean
                setLastUnremovedScurveMean = True
            if (thrDacVal < 50 and sigmaHighThrDacChiSquaredOverNdof < 0.5 and scurveSigma - scurveSigmaError > sigmaHighThrDacPlusError and scurveMean > 6 and scurveMean > lastUnremovedScurveMean) or (scurveMean > 2*lastUnremovedScurveMean):
#            if (thrDacVal < 50 and sigmaHighThrDacChiSquaredOverNdof < 0.5 and scurveSigma - scurveSigmaError > sigmaHighThrDacPlusError and scurveMean > 6 and scurveMean > lastUnremovedScurveMean) or (thrDacVal < 60 and scurveMean > 45) or (scurveMean > 6 and scurveMean > 2*lastUnremovedScurveMean):
                continue
            lastUnremovedScurveMean = scurveMean
            tgraph_scurveMeanVsThrDacForFit.SetPoint(tgraph_scurveMeanVsThrDacForFit.GetN(),thrDacVal,scurveMean)
            tgraph_scurveMeanVsThrDacForFit.SetPointError(tgraph_scurveMeanVsThrDacForFit.GetN()-1,0,scurveMeanError)

        #a 4th order polynomial expanded about the lower edge of the fit range    
        def quartic(x,par):    
            return (par[0]*pow((x[0]-min(fitRange)),4)+par[1]*pow((x[0]-min(fitRange)),3))+par[2]*pow((x[0]-min(fitRange)),2)+par[3]*(x[0]-min(fitRange))+par[4]    
            
        # Mean vs CFG_THR_*_DAC
        dict_canvScurveMeanVsThrDac[vfat] = r.TCanvas("canvScurveMeanVsThrDac_{0}".format(suffix),"Scurve Mean vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanVsThrDac[vfat].cd()
        dict_ScurveMeanVsThrDac[vfat].Draw("APE1")
        dict_ScurveMeanVsThrDac[vfat].GetXaxis().SetTitle(thrDacName)
        dict_ScurveMeanVsThrDac[vfat].GetYaxis().SetTitle("Scurve Mean #left(fC#right)")
        dict_ScurveMeanVsThrDac[vfat].Draw("APE1")
#        dict_funcScurveMeanVsThrDac[vfat] = r.TF1("func_{0}".format((dict_ScurveMeanVsThrDac[vfat].GetName()).strip('g')),"[0]*x^4+[1]*x^3+[2]*x^2+[3]*x+[4]",min(fitRange), max(fitRange) )
        dict_funcScurveMeanVsThrDac[vfat] = r.TF1("func_{0}".format((dict_ScurveMeanVsThrDac[vfat].GetName()).strip('g')),quartic,min(fitRange),max(fitRange),5)
        #require the first derivative to be positive at the lower boundary of the fit range 
        dict_funcScurveMeanVsThrDac[vfat].SetParLimits(3,0,1000000) 
        tgraph_scurveMeanVsThrDacForFit.Fit(dict_funcScurveMeanVsThrDac[vfat],"QR")
        dict_ScurveMeanVsThrDac[vfat].Write()
        dict_funcScurveMeanVsThrDac[vfat].Write()

        # Mean vs CFG_THR_*_DAC - Box Plot
        dict_canvScurveMeanVsThrDac_BoxPlot[vfat] = r.TCanvas("canvScurveMeanVsThrDac_BoxPlot_{0}".format(suffix),"Box Plot: Scurve Mean vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanVsThrDac_BoxPlot[vfat].cd()
        dict_ScurveMeanVsThrDac_BoxPlot[vfat].Draw("candle1")
        dict_ScurveMeanVsThrDac_BoxPlot[vfat].Write()

        # Sigma vs CFG_THR_*_DAC
        dict_canvScurveSigmaVsThrDac[vfat] = r.TCanvas("canvScurveSigmaVsThrDac_{0}".format(suffix),"Scurve Sigma vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaVsThrDac[vfat].cd()
        dict_ScurveSigmaVsThrDac[vfat].Draw("APE1")
        dict_ScurveSigmaVsThrDac[vfat].GetXaxis().SetTitle(thrDacName)
        dict_ScurveSigmaVsThrDac[vfat].GetYaxis().SetTitle("Scurve Sigma #left(fC#right)")
        dict_ScurveSigmaVsThrDac[vfat].Draw("APE1")
        func_ScurveSigmaVsThrDac = r.TF1("func_{0}".format((dict_ScurveSigmaVsThrDac[vfat].GetName()).strip('g')),"[0]",min(fitRange), max(fitRange) )
        dict_ScurveSigmaVsThrDac[vfat].Fit(func_ScurveSigmaVsThrDac,"QR")
        dict_ScurveSigmaVsThrDac[vfat].Write()
        func_ScurveSigmaVsThrDac.Write()

        # Sigma vs CFG_THR_*_DAC - Box Plot
        dict_canvScurveSigmaVsThrDac_BoxPlot[vfat] = r.TCanvas("canvScurveSigmaVsThrDac_BoxPlot_{0}".format(suffix),"Box Plot: Scurve Sigma vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].cd()
        dict_ScurveSigmaVsThrDac_BoxPlot[vfat].Draw("candle1")
        dict_ScurveSigmaVsThrDac_BoxPlot[vfat].Write()

        # Write CFG_THR_*_DAC calibration file
        calThrDacFile.write("{0}\t{1}\t{2}\n".format(
            vfat,
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(0),
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(1))
            )

        # Draw Legend?
        if not args.noLeg:
            dict_canvScurveMeanByThrDac[vfat].cd()
            legArmDacValues.Draw("same")

            dict_canvScurveSigmaByThrDac[vfat].cd()
            legArmDacValues.Draw("same")
            pass

        # Store Canvases
        dict_canvScurveMeanByThrDac[vfat].Write()
        dict_canvScurveSigmaByThrDac[vfat].Write()
        dict_canvScurveMeanVsThrDac[vfat].Write()
        dict_canvScurveSigmaVsThrDac[vfat].Write()
        dict_canvScurveMeanVsThrDac_BoxPlot[vfat].Write()
        dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].Write()

        # Print info to user
        vfatOrAll = vfat
        if vfat == -1:
            vfatOrAll == "All"
        print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
            vfatOrAll,
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(0),
            dict_funcScurveMeanVsThrDac[vfat].GetParError(0),
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(1),
            dict_funcScurveMeanVsThrDac[vfat].GetParError(1),
            func_ScurveSigmaVsThrDac.GetParameter(0),
            func_ScurveSigmaVsThrDac.GetParError(1))
            )

    if args.savePlots:
        for vfat in range(-1,24):
            dict_canvScurveMeanByThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveMeanByThrDac[vfat].GetName()))
            dict_canvScurveSigmaByThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveSigmaByThrDac[vfat].GetName()))
            dict_canvScurveMeanVsThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveMeanVsThrDac[vfat].GetName()))
            dict_canvScurveSigmaVsThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveSigmaVsThrDac[vfat].GetName()))
            dict_canvScurveMeanVsThrDac_BoxPlot[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveMeanVsThrDac_BoxPlot[vfat].GetName()))
            dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].GetName()))
    
    # Make summary canvases, always save these
    canvScurveMeanByThrDac_Summary = make3x8Canvas("canvScurveMeanByThrDac_Summary",dict_mGraphScurveMean,"APE1")
    canvScurveSigmaByThrDac_Summary = make3x8Canvas("canvScurveSigmaByThrDac_Summary",dict_mGraphScurveSigma,"APE1")
    canvScurveMeanVsThrDac_Summary = make3x8Canvas("canvScurveMeanVsThrDac_Summary",dict_ScurveMeanVsThrDac,"APE1",dict_funcScurveMeanVsThrDac)
    canvScurveSigmaVsThrDac_Summary = make3x8Canvas("canvScurveSigmaVsThrDac_Summary",dict_ScurveSigmaVsThrDac,"APE1")
    canvScurveMeanVsThrDac_BoxPlot_Summary = make3x8Canvas("canvScurveMeanVsThrDac_BoxPlot_Summary",dict_ScurveMeanVsThrDac_BoxPlot,"candle1")
    canvScurveSigmaVsThrDac_BoxPlot_Summary = make3x8Canvas("canvScurveSigmaVsThrDac_BoxPlot_Summary",dict_ScurveSigmaVsThrDac_BoxPlot,"candle1")

    # Draw Legend?
    if not args.noLeg:
        canvScurveMeanByThrDac_Summary.cd(1)
        legArmDacValues.Draw("same")

        canvScurveSigmaByThrDac_Summary.cd(1)
        legArmDacValues.Draw("same")

    # Save summary canvases (alwasys)
    print("\nSaving Summary TCanvas Objects")
    canvScurveMeanByThrDac_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvScurveMeanByThrDac_Summary.GetName()))
    canvScurveSigmaByThrDac_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigmaByThrDac_Summary.GetName()))
    canvScurveMeanVsThrDac_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvScurveMeanVsThrDac_Summary.GetName()))
    canvScurveSigmaVsThrDac_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigmaVsThrDac_Summary.GetName()))
    canvScurveMeanVsThrDac_BoxPlot_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvScurveMeanVsThrDac_BoxPlot_Summary.GetName()))
    canvScurveSigmaVsThrDac_BoxPlot_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigmaVsThrDac_BoxPlot_Summary.GetName()))

    # Close output files
    outFile.Close()
    calThrDacFile.close()

    print("\nYour calibration file is located in:")
    print("\n\t{0}/calFile_{2}_{1}.txt\n".format(elogPath,chamberName,thrDacName))

    print("You can find all ROOT objects in:")
    print("\n\t{0}/calFile_{2}_{1}.root\n".format(elogPath,chamberName,thrDacName))

    print("You can find all plots in:")
    print("\n\t{0}\n".format(elogPath))

    print("Done")
