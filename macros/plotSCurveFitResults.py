#!/bin/env python

"""
``plotSCurveFitResults.py`` --- Compare S-curves results across scandates
=========================================================================

Synopsis
--------

**plotSCurveFitResults.py** :token:`--anaType` <*ANALYSIS NAME*> :token:`-i`
<*LIST OF SCAN DATES FILE*> [*OPTIONS*]

Description
-----------

While :program:`gemTreeDrawWrapper.py` and :program:`gemPlotter.py` allow you to
plot observables from multiple runs sometimes you are interested in seeing the
results made from :program:`anaUltraScurve.py`, from multiple scandates, on the
same set of ``TCanvas``.  The tool :program:`plotSCurveFitResults.py` allows you
to do this.  The tool will create five output ``*.png`` files and one ``TFile``
which stores relevant plots for each VFAT from each of the input scandates.
These five ``*.png`` files are:

* ``scurveFitSummaryGridAllScandates.png``, shows the ``fitSummary`` curves from
  all input scandates on one ``TCanvas`` in a 3-by-8 grid,
* ``scurveMeanGridAllScandates.png``, shows the distribution of s-curve mean
  positions from each VFAT from all input scandates on one `TCanvas` in a 3-by-8
  grid,
* ``scurveSigmaGridAllScandates.png``, as ``scurveMeanGridAllScandates.png`` but
  for S-curve sigma,
* ``canvSCurveSigmaDetSumAllScandates.png``, shows a summary distribution of
  S-curve sigma positions from all VFATs of the detector from all scandates on
  one ``TCanvas``, and
* ``canvSCurveMeanDetSumAllScandates.png``, as
  ``canvSCurveSigmaDetSumAllScandates.png`` but for S-curve mean.

The files will be found in :envvar:`ELOG_PATH` along with the output ``TFile``,
named ``scurveFitResultPlots.root``.

Arguments
---------

.. program:: plotSCurveFitResults.py

.. option:: -i, --infilename <FILE>

    Physical filename of the input file to be passed to
    :program:`plotSCurveFitResults.py`. The format of this input file should
    follow the :doc:`Three Column Format </scandate-list-formats>`.

.. option:: --alphaLabels

    When providing this flag :program:`plotSCurveFitResults.py` will interpret
    the **Indep. Variable** as a string.

.. option:: --anaType <ANALYSIS TYPE>

    Analysis type to be executed, one of ``scurveAna`` or ``trimAna``.

.. option:: --drawLeg

    Draws a ``TLegend`` on the output plots. For those 3x8 grid plots the legend
    will only be drawn on the plot for VFAT0.

.. option:: --rootName <FILE NAME>

    Name of output ``TFile``.  This file will be found in :envvar:`ELOG_PATH`.

.. option:: --rootOpt <STRING>

    Option for creating the output ``TFile``, e.g. ``RECREATE`` or ``UPDATE``.

.. option:: --ztrim <NUMBER>

    The ztrim value that was used when running the scans listed in
    :token:`--infilename`.

Input File
----------

The format of this input file should follow the :doc:`Three Column Format
</scandate-list-formats>`.  Note that here the **Indep. Variable** for each row
will be used as the ``TLegend`` entry if the :option:`--drawLeg` argument is
supplied.

Example
-------

To plot results from a set of scandates defined in
``listOfScanDates_Scurve.txt`` taken by either :program:`ultraScurve.py` or
:program:`trimChamber.py` and analyzed with :program:`anaUltraScurve.py` you
would call:

.. code-block:: bash

    plotSCurveFitResults.py --anaType=scurveAna --drawLeg -i listOfScanDates_Scurve.txt --alphaLabels

This will produce the five ``*.png`` files mentioned above along with the output
``TFile``.

Environment
-----------

.. glossary::

    :envvar:`DATA_PATH`
        The location of input data

    :envvar:`ELOG_PATH`
        Results are written in the directory pointed to by this variable
"""

if __name__ == '__main__':
    from gempython.gemplotting.utils.anaInfo import tree_names
    from gempython.gemplotting.utils.anautilities import getCyclicColor, getDirByAnaType, filePathExists, getSummaryCanvasByiEta, getSummaryCanvas, parseListOfScanDatesFile
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import envCheck, runCommand
    from gempython.gemplotting.macros.plotoptions import parser
    from gempython.gemplotting.macros.scurvePlottingUtitilities import overlay_scurve

    import os
    import ROOT as r

    parser.add_option("--alphaLabels", action="store_true", dest="alphaLabels",
                    help="Draw output plot using alphanumeric lables instead of pure floating point", metavar="alphaLabels")
    parser.add_option("--anaType", type="string", dest="anaType",
                    help="Analysis type to be executed, from list {'scurveAna','trimAna'}", metavar="anaType")
    parser.add_option("--drawLeg", action="store_true", dest="drawLeg",
                    help="When used with --summary option draws a TLegend on the output plot", metavar="drawLeg")
    parser.add_option("--rootName", type="string", dest="rootName", default="scurveFitResultPlots.root",
                    help="Name for the output TFile, will be found in ELOG_PATH", metavar="rootName")
    parser.add_option("--rootOpt", type="string", dest="rootOpt", default="RECREATE",
                    help="Option for the output TFile, e.g. {'RECREATE','UPDATE'}", metavar="rootOpt")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                    help="Specify the p value of the trim", metavar="ztrim")

    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()

    # Suppress all pop-ups from ROOT
    r.gROOT.SetBatch(True)

    # Check Paths
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath  = os.getenv('ELOG_PATH')

    gemType = "ge11"

    # Check anaType is understood
    supportedAnaTypes = ['scurveAna','trimAna']
    if options.anaType not in supportedAnaTypes:
        print("Invalid analysis specificed, please select only from the list:")
        print(supportedAnaTypes)
        exit(os.EX_USAGE)
        pass

    # Get info from input file
    parsedTuple = parseListOfScanDatesFile(options.filename, options.alphaLabels)
    listChamberAndScanDate = parsedTuple[0]

    # Define nested dictioniaries
    #   Outer key -> (chamberName,scandate) tuple
    #   Inner key -> vfat position
    dict_fitSum = ndict()
    dict_ScurveMean = ndict() # Inner key: (0,23) follows vfat #, -1 is summary over all det
    dict_ScurveSigma = ndict()
    dict_ScurveEffPed = ndict()

    dict_ScurveMeanByiEta = ndict()
    dict_ScurveSigmaByiEta = ndict()

    dict_ScurveEffPed_boxPlot = {}  # key: (chamberName,scandate)
    dict_ScurveThresh_boxPlot = {}  # key: (chamberName,scandate)
    dict_ScurveSigma_boxPlot = {}  # key: (chamberName,scandate)

    from gempython.tools.hw_constants import vfatsPerGemVariant
    from gempython.gemplotting.mapping.chamberInfo import chamber_maxiEtaiPhiPair
    maxiEta, maxiPhi = chamber_maxiEtaiPhiPair[gemType]
    
    # Get the plots from all files
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType(options.anaType.strip("Ana"), chamberAndScanDatePair[0], options.ztrim)
        if not filePathExists(dirPath, chamberAndScanDatePair[1]):
            print('Filepath {0}/{1} does not exist!'.format(dirPath, chamberAndScanDatePair[1]))
            print('Please cross-check, exiting!')
            outF.Close()
            exit(os.EX_DATAERR)
        filename = "{0}/{1}/{2}".format(dirPath, chamberAndScanDatePair[1], tree_names[options.anaType][0])

        # Load the file
        r.TH1.AddDirectory(False)
        scanFile   = r.TFile(filename,"READ")
        
        # Get all plots from scanFile - vfat level
        for vfat in range(0,vfatsPerGemVariant[gemType]):
            # Fit summary
            dict_fitSum[chamberAndScanDatePair][vfat] = scanFile.Get("VFAT{0}/gFitSummary_VFAT{0}".format(vfat))
            dict_fitSum[chamberAndScanDatePair][vfat].SetName(
                    "{0}_{1}_{2}".format(
                        dict_fitSum[chamberAndScanDatePair][vfat].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_fitSum[chamberAndScanDatePair][vfat].SetLineColor(getCyclicColor(idx))
            dict_fitSum[chamberAndScanDatePair][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_fitSum[chamberAndScanDatePair][vfat].SetMarkerStyle(20+idx)

            # Scurve Mean
            dict_ScurveMean[chamberAndScanDatePair][vfat] = scanFile.Get("VFAT{0}/gScurveMeanDist_vfat{0}".format(vfat))
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveMean[chamberAndScanDatePair][vfat].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetLineColor(getCyclicColor(idx))
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetMarkerStyle(20+idx)

            # Scurve Width
            dict_ScurveSigma[chamberAndScanDatePair][vfat] = scanFile.Get("VFAT{0}/gScurveSigmaDist_vfat{0}".format(vfat))
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveSigma[chamberAndScanDatePair][vfat].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetLineColor(getCyclicColor(idx))
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetMarkerStyle(20+idx)

            pass

        for ieta in range(1,maxiEta+1):
            # Scurve Mean
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta] = scanFile.Get("Summary/ieta{0}/gScurveMeanDist_ieta{0}".format(ieta))
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetLineColor(getCyclicColor(idx))
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetMarkerStyle(20+idx)

            # Scurve Sigma
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta] = scanFile.Get("Summary/ieta{0}/gScurveSigmaDist_ieta{0}".format(ieta))
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta].SetLineColor(getCyclicColor(idx))
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta].SetMarkerStyle(20+idx)
            pass

        # Get the detector level plots
        dict_ScurveMean[chamberAndScanDatePair][-1] = scanFile.Get("Summary/gScurveMeanDist_All")
        dict_ScurveMean[chamberAndScanDatePair][-1].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveMean[chamberAndScanDatePair][-1].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        dict_ScurveMean[chamberAndScanDatePair][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveMean[chamberAndScanDatePair][-1].SetMarkerColor(getCyclicColor(idx))
        dict_ScurveMean[chamberAndScanDatePair][-1].SetMarkerStyle(20+idx)

        dict_ScurveSigma[chamberAndScanDatePair][-1] = scanFile.Get("Summary/gScurveSigmaDist_All")
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveSigma[chamberAndScanDatePair][-1].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetMarkerColor(getCyclicColor(idx))
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetMarkerStyle(20+idx)

        dict_ScurveEffPed[chamberAndScanDatePair][-1] = scanFile.Get("Summary/hScurveEffPedDist_All")
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveEffPed[chamberAndScanDatePair][-1].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetMarkerColor(getCyclicColor(idx))
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetMarkerStyle(20+idx)

        dict_ScurveEffPed_boxPlot[chamberAndScanDatePair] = scanFile.Get("Summary/ScurveEffPed_All")
        dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )

        dict_ScurveThresh_boxPlot[chamberAndScanDatePair] = scanFile.Get("Summary/ScurveMean_All")
        dict_ScurveThresh_boxPlot[chamberAndScanDatePair].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveThresh_boxPlot[chamberAndScanDatePair].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )

        dict_ScurveSigma_boxPlot[chamberAndScanDatePair] = scanFile.Get("Summary/ScurveSigma_All")
        dict_ScurveSigma_boxPlot[chamberAndScanDatePair].SetName(
                    "{0}_{1}_{2}".format(
                        dict_ScurveSigma_boxPlot[chamberAndScanDatePair].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        pass

    # Define the TMultiGraph dictionaries
    dict_mGraph_fitSum = ndict()        # key: (0,23) follows vfat #
    dict_mGraph_ScurveMean = ndict()    # key: (0,23) follows vfat #, -1 is summary over all det
    dict_mGraph_ScurveSigma = ndict()   # key: (0,23) follows vfat #, -1 is summary over all det


    dict_mGraph_ScurveMean[-1] = r.TMultiGraph("mGraph_ScurveMeanDist_All","")
    dict_mGraph_ScurveMean[-1].GetXaxis().SetTitle("scurve mean #left(fC#right)")

    dict_mGraph_ScurveSigma[-1] = r.TMultiGraph("mGraph_ScurveSigmaDist_All","")
    dict_mGraph_ScurveSigma[-1].GetXaxis().SetTitle("scurve sigma #left(fC#right)")

    dict_mGraph_ScurveMeanByiEta = ndict()
    dict_mGraph_ScurveSigmaByiEta = ndict()

    # Make the canvas dictionaries
    dict_canvSCurveFitSum = ndict()
    dict_canvSCurveMean = ndict()
    dict_canvSCurveMeanByiEta = ndict()
    dict_canvSCurveSigma = ndict()
    dict_canvSCurveSigmaByiEta = ndict()

    # Make the summary canvases
    canvScurveMean_DetSum = r.TCanvas("canvSCurveMeanDetSumAllScandates","Scurve Mean - Detector Summary",600,600)
    canvScurveSigma_DetSum = r.TCanvas("canvSCurveSigmaDetSumAllScandates","Scurve Sigma - Detector Summary",600,600)
    canvScurveEffPed_DetSum = r.TCanvas("canvSCurveEffPedDetSumAllScandates","Scurve EffPed - Detector Summary",600,600)
    canvScurveEffPed_boxPlot = r.TCanvas("canvSCurveEffPed_boxPlot","Scurve EffPed - Detector Summary boxPlot",600,600)
    canvScurveThresh_boxPlot = r.TCanvas("canvSCurveMean_boxPlot","Scurve Mean - Detector Summary boxPlot",600,600)
    canvScurveSigma_boxPlot = r.TCanvas("canvSCurveSigma_boxPlot","Scurve Sigma - Detector Summary boxPlot",600,600)
    plotLeg = r.TLegend(0.1,0.65,0.45,0.9)
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        drawOpt="APE1"

        # Draw per VFAT distributions
        for vfat in range(0,vfatsPerGemVariant[gemType]):
            if idx == 0:
                dict_mGraph_fitSum[vfat]    = r.TMultiGraph("mGraph_FitSummary_VFAT{0}".format(vfat),"VFAT{0}".format(vfat))
                dict_mGraph_ScurveMean[vfat]= r.TMultiGraph("mGraph_ScurveMeanDist_vfat{0}".format(vfat),"VFAT{0}".format(vfat))
                dict_mGraph_ScurveSigma[vfat]=r.TMultiGraph("mGraph_ScurveSigmaDist_vfat{0}".format(vfat),"VFAT{0}".format(vfat))

                dict_canvSCurveFitSum[vfat] = r.TCanvas("canvScurveFitSum_VFAT{0}".format(vfat),"SCurve Fit Summary - VFAT{0}".format(vfat),600,600)
                dict_canvSCurveMean[vfat]   = r.TCanvas("canvScurveMean_VFAT{0}".format(vfat),"SCurve Mean - VFAT{0}".format(vfat),600,600)
                dict_canvSCurveSigma[vfat]  = r.TCanvas("canvScurveSigma_VFAT{0}".format(vfat),"SCurve Sigma - VFAT{0}".format(vfat),600,600)
                pass

            dict_mGraph_fitSum[vfat].Add(dict_fitSum[chamberAndScanDatePair][vfat])
            dict_mGraph_ScurveMean[vfat].Add(dict_ScurveMean[chamberAndScanDatePair][vfat])
            dict_mGraph_ScurveSigma[vfat].Add(dict_ScurveSigma[chamberAndScanDatePair][vfat])

            if (idx == (len(listChamberAndScanDate) - 1) ):
                chanStripOrPanPin = dict_fitSum[chamberAndScanDatePair][vfat].GetXaxis().GetTitle()

                dict_canvSCurveFitSum[vfat].cd()
                dict_mGraph_fitSum[vfat].Draw(drawOpt) # The axis doesn't exist unless we draw it first, ROOT magic =/
                dict_mGraph_fitSum[vfat].GetXaxis().SetTitle(chanStripOrPanPin)
                dict_mGraph_fitSum[vfat].GetYaxis().SetTitle("Threshold #left(fC#right)")
                dict_mGraph_fitSum[vfat].Draw(drawOpt)

                dict_canvSCurveMean[vfat].cd()
                dict_mGraph_ScurveMean[vfat].Draw(drawOpt)
                dict_mGraph_ScurveMean[vfat].GetXaxis().SetTitle("scurve mean #left(fC#right)")
                dict_mGraph_ScurveMean[vfat].Draw(drawOpt)

                dict_canvSCurveSigma[vfat].cd()
                dict_mGraph_ScurveSigma[vfat].Draw(drawOpt)
                dict_mGraph_ScurveSigma[vfat].GetXaxis().SetTitle("scurve sigma #left(fC#right)")
                dict_mGraph_ScurveSigma[vfat].GetXaxis().SetRangeUser(0.,10.)
                dict_mGraph_ScurveSigma[vfat].Draw(drawOpt)
                pass
            pass

        # Draw per ieta distributions
        for ieta in range(1,maxiEta+1):
            if idx == 0:
                dict_mGraph_ScurveMeanByiEta[ieta] = r.TMultiGraph("mGraph_ScurveMeanDist_ieta{0}".format(ieta),"i#eta = {0}".format(ieta))
                dict_mGraph_ScurveSigmaByiEta[ieta] = r.TMultiGraph("mGraph_ScurveSigmaDist_ieta{0}".format(ieta),"i#eta = {0}".format(ieta))

                dict_canvSCurveMeanByiEta[ieta]   = r.TCanvas("canvScurveMean_ieta{0}".format(ieta),"SCurve Mean - ieta{0}".format(ieta),600,600)
                dict_canvSCurveSigmaByiEta[ieta]  = r.TCanvas("canvScurveSigma_ieta{0}".format(ieta),"SCurve Sigma - ieta{0}".format(ieta),600,600)
                pass

            dict_mGraph_ScurveMeanByiEta[ieta].Add(dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta])
            dict_mGraph_ScurveSigmaByiEta[ieta].Add(dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta])

            if (idx == (len(listChamberAndScanDate) - 1) ):
                dict_canvSCurveMeanByiEta[ieta].cd()
                dict_mGraph_ScurveMeanByiEta[ieta].Draw(drawOpt)
                dict_mGraph_ScurveMeanByiEta[ieta].GetXaxis().SetTitle("scurve mean #left(fC#right)")
                dict_mGraph_ScurveMeanByiEta[ieta].Draw(drawOpt)

                dict_canvSCurveSigmaByiEta[ieta].cd()
                dict_mGraph_ScurveSigmaByiEta[ieta].Draw(drawOpt)
                dict_mGraph_ScurveSigmaByiEta[ieta].GetXaxis().SetTitle("scurve sigma #left(fC#right)")
                dict_mGraph_ScurveSigmaByiEta[ieta].GetXaxis().SetRangeUser(0.,10.)
                dict_mGraph_ScurveSigmaByiEta[ieta].Draw(drawOpt)
                pass
            pass

        dict_mGraph_ScurveMean[-1].Add(dict_ScurveMean[chamberAndScanDatePair][-1])
        dict_mGraph_ScurveSigma[-1].Add(dict_ScurveSigma[chamberAndScanDatePair][-1])

        canvScurveEffPed_DetSum.cd()
        if idx == 0:
            dict_ScurveEffPed[chamberAndScanDatePair][-1].Draw("E1")
        else:
            dict_ScurveEffPed[chamberAndScanDatePair][-1].Draw("sameE1")

        dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].SetFillColorAlpha(getCyclicColor(idx), 0.3)
        dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].SetLineColor(getCyclicColor(idx))

        dict_ScurveThresh_boxPlot[chamberAndScanDatePair].SetFillColorAlpha(getCyclicColor(idx), 0.3)
        dict_ScurveThresh_boxPlot[chamberAndScanDatePair].SetLineColor(getCyclicColor(idx))

        dict_ScurveSigma_boxPlot[chamberAndScanDatePair].SetFillColorAlpha(getCyclicColor(idx), 0.3)
        dict_ScurveSigma_boxPlot[chamberAndScanDatePair].SetLineColor(getCyclicColor(idx))
        if idx == 0:
            dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].GetXaxis().SetTitle("VFAT position")
            dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].GetYaxis().SetTitle("Effective Pedestal #left(A.U.#right)")

            dict_ScurveThresh_boxPlot[chamberAndScanDatePair].GetXaxis().SetTitle("VFAT position")
            dict_ScurveThresh_boxPlot[chamberAndScanDatePair].GetYaxis().SetTitle("Threshold #left(fC#right)")

            dict_ScurveSigma_boxPlot[chamberAndScanDatePair].GetXaxis().SetTitle("VFAT position")
            dict_ScurveSigma_boxPlot[chamberAndScanDatePair].GetYaxis().SetTitle("Noise #left(fC#right)")

            canvScurveEffPed_boxPlot.cd()
            dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].Draw("candle1")

            canvScurveThresh_boxPlot.cd()
            dict_ScurveThresh_boxPlot[chamberAndScanDatePair].Draw("candle1")

            canvScurveSigma_boxPlot.cd()
            dict_ScurveSigma_boxPlot[chamberAndScanDatePair].Draw("candle1")
        else:
            canvScurveEffPed_boxPlot.cd()
            dict_ScurveEffPed_boxPlot[chamberAndScanDatePair].Draw("candle1 same")
            canvScurveThresh_boxPlot.cd()
            dict_ScurveThresh_boxPlot[chamberAndScanDatePair].Draw("candle1 same")
            canvScurveSigma_boxPlot.cd()
            dict_ScurveSigma_boxPlot[chamberAndScanDatePair].Draw("candle1 same")

            pass

        # Fill Legend - use VFAT0 of each
        plotLeg.AddEntry(dict_fitSum[chamberAndScanDatePair][0],chamberAndScanDatePair[2],"LPE")
        pass

    # Draw multigraphs for summary cases
    canvFitSum_Grid = getSummaryCanvas(dict_mGraph_fitSum, name="scurveFitSummaryGridAllScandates", drawOpt="APE1", gemType=gemType)
    canvScurveMean_Grid = getSummaryCanvas(dict_mGraph_ScurveMean, name="scurveMeanGridAllScandates", drawOpt="APE1", gemType=gemType)
    canvScurveSigma_Grid = getSummaryCanvas(dict_mGraph_ScurveSigma, name="scurveSigmaGridAllScandates", drawOpt="APE1", gemType=gemType)

    canvScurveMean_Grid_iEta = getSummaryCanvasByiEta(dict_mGraph_ScurveMeanByiEta, name="scurveMeanGridByiEtaAllScandates", drawOpt="APE1", gemType=gemType)
    canvScurveSigma_Grid_iEta = getSummaryCanvasByiEta(dict_mGraph_ScurveSigmaByiEta, name="scurveSigmaGridByiEtaAllScandates", drawOpt="APE1", gemType=gemType)

    canvScurveMean_DetSum.cd()
    canvScurveMean_DetSum.cd().SetLogy()
    dict_mGraph_ScurveMean[-1].Draw("APE1")
    #dict_mGraph_ScurveMean[-1].GetXaxis().SetRangeUser(0,40)
    #dict_mGraph_ScurveMean[-1].GetYaxis().SetRangeUser(1e-1,1e3)
    #dict_mGraph_ScurveMean[-1].Draw("APE1")

    canvScurveSigma_DetSum.cd()
    canvScurveSigma_DetSum.cd().SetLogy()
    dict_mGraph_ScurveSigma[-1].Draw("APE1")
    dict_mGraph_ScurveSigma[-1].GetXaxis().SetRangeUser(0,10)
    #dict_mGraph_ScurveSigma[-1].GetYaxis().SetRangeUser(1e-1,1e3)
    dict_mGraph_ScurveSigma[-1].Draw("APE1")

    canvScurveEffPed_DetSum.cd().SetLogy()

    if options.drawLeg:
        # VFAT level
        for vfat in range(0,vfatsPerGemVariant[gemType]):
            dict_canvSCurveFitSum[vfat].cd()
            plotLeg.Draw("same")

            dict_canvSCurveMean[vfat].cd()
            plotLeg.Draw("same")

            dict_canvSCurveSigma[vfat].cd()
            plotLeg.Draw("same")
            pass

        # ieta level
        for ieta in range(1,maxiEta+1):
            dict_canvSCurveMeanByiEta[ieta].cd()
            plotLeg.Draw("same")

            dict_canvSCurveSigmaByiEta[ieta].cd()
            plotLeg.Draw("same")
            pass

        # Draw legend once at the vfat level
        canvFitSum_Grid.cd(1)
        plotLeg.Draw("same")

        canvScurveMean_Grid.cd(1)
        plotLeg.Draw("same")

        canvScurveSigma_Grid.cd(1)
        plotLeg.Draw("same")

        # Draw legend once at the ieta level
        canvScurveMean_Grid_iEta.cd(1)
        plotLeg.Draw("same")

        canvScurveSigma_Grid_iEta.cd(1)
        plotLeg.Draw("same")

        # Draw legend at the detector level
        canvScurveMean_DetSum.cd()
        plotLeg.Draw("same")

        canvScurveSigma_DetSum.cd()
        plotLeg.Draw("same")

        canvScurveEffPed_DetSum.cd()
        plotLeg.Draw("same")

        canvScurveEffPed_boxPlot.cd()
        plotLeg.Draw("same")

        canvScurveThresh_boxPlot.cd()
        plotLeg.Draw("same")

        canvScurveSigma_boxPlot.cd()
        plotLeg.Draw("same")
        pass

    # Make output images
    canvFitSum_Grid.SaveAs("{0}/{1}.png".format(elogPath,canvFitSum_Grid.GetName()))
    canvScurveMean_Grid.SaveAs("{0}/{1}.png".format(elogPath,canvScurveMean_Grid.GetName()))
    canvScurveSigma_Grid.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigma_Grid.GetName()))

    canvScurveMean_Grid_iEta.SaveAs("{0}/{1}.png".format(elogPath,canvScurveMean_Grid_iEta.GetName()))
    canvScurveSigma_Grid_iEta.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigma_Grid_iEta.GetName()))

    canvScurveMean_DetSum.SaveAs("{0}/{1}.png".format(elogPath,canvScurveMean_DetSum.GetName()))
    canvScurveSigma_DetSum.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigma_DetSum.GetName()))
    canvScurveEffPed_DetSum.SaveAs("{0}/{1}.png".format(elogPath,canvScurveEffPed_DetSum.GetName()))
    canvScurveEffPed_boxPlot.SaveAs("{0}/{1}.png".format(elogPath,canvScurveEffPed_boxPlot.GetName()))
    canvScurveThresh_boxPlot.SaveAs("{0}/{1}.png".format(elogPath,canvScurveThresh_boxPlot.GetName()))
    canvScurveSigma_boxPlot.SaveAs("{0}/{1}.png".format(elogPath,canvScurveSigma_boxPlot.GetName()))

    # Save summary canvas objects in output root file
    outF = r.TFile("{0}/{1}".format(elogPath,options.rootName),options.rootOpt)

    for vfat in range(0,vfatsPerGemVariant[gemType]):
        dirVFAT = outF.mkdir("VFAT{0}".format(vfat))
        dirVFAT.cd()

        dict_canvSCurveFitSum[vfat].Write()
        dict_mGraph_fitSum[vfat].Write()

        dict_canvSCurveMean[vfat].Write()
        dict_mGraph_ScurveMean[vfat].Write()

        dict_canvSCurveSigma[vfat].Write()
        dict_mGraph_ScurveSigma[vfat].Write()
        pass

    dirSummary = outF.mkdir("Summary")
    for ieta in range(1,maxiEta+1):
        dir_iEta = dirSummary.mkdir("ieta{0}".format(ieta))
        dir_iEta.cd()

        dict_canvSCurveMeanByiEta[ieta].Write()
        dict_mGraph_ScurveMeanByiEta[ieta].Write()

        dict_canvSCurveSigmaByiEta[ieta].Write()
        dict_mGraph_ScurveSigmaByiEta[ieta].Write()
        pass

    dirSummary.cd()
    canvFitSum_Grid.Write()
    canvScurveMean_Grid.Write()
    canvScurveMean_Grid_iEta.Write()
    canvScurveSigma_Grid.Write()
    canvScurveSigma_Grid_iEta.Write()
    canvScurveMean_DetSum.Write()
    dict_mGraph_ScurveMean[-1].Write()
    canvScurveSigma_DetSum.Write()
    dict_mGraph_ScurveSigma[-1].Write()
    canvScurveEffPed_DetSum.Write()
    canvScurveEffPed_boxPlot.Write()
    canvScurveThresh_boxPlot.Write()
    canvScurveSigma_boxPlot.Write()

    print("Your plots can be found in:")
    print("")
    print("     {0}".format(elogPath))
    print("")

    print("You can open the output TFile via:")
    print("")
    print("     root -l {0}/{1}".format(elogPath,options.rootName))

    print("")
    print("Good-bye")
