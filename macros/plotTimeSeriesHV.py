#!/usr/bin/env python

r"""
``plotTimeSeriesHV.py`` --- Plotting DCS Plots On Common TCanvas
================================================================

Synopsis
--------

**plotTimeSeriesHV.py** [*OPTIONS*] [INPUTFILE] [QC8_ROW] [QC8_COLUMN]

Description
-----------

Plots HV plots made with :program:`StatusVmon904HV.py` onto several common TCanvas objects
and creates images of those TCanvas for faster analysis.  Additionally these output
TCanvas objects will be stored in an output TFile, which is by default:

    $ELOG_PATH/DCS_PLOTS

Arguments
---------

Mandatory arguments
...................

The following list shows the mandatory inputs that must be supplied to execute this script:

.. program:: plotTimeSeriesHV.py

.. option:: inputfile

    Input file coming from StatusVmon904HV.py

.. option:: row

    Row of the QC8 stand, see `StandNomenclature.png <https://twiki.cern.ch/twiki/pub/CMS/GEMQC8WEEKLYPLAN/StandNomenclature.png>`_.

.. option:: column
    
    Column of the QC8 stand, see `StandNomenclature.png <https://twiki.cern.ch/twiki/pub/CMS/GEMQC8WEEKLYPLAN/StandNomenclature.png>`_.

.. option:: -t, --top

    Specifies top layer, mutually exclusive with :token:`--bot`.

.. option:: -b, --bot

    Specifies bot layer, mutually exclusive with :token:`--top`.

.. option:: -d, --debug

    Prints additional debugging info

.. option:: -o, --outfilename

    Name of output TFile that will be created and store the TCanvas objects

.. option:: -u, --update

    The TFile specified by :token:`--outfilename` will be appended rather than overwritten

Example
-------

Calling the following:

.. code-block:: bash

    plotTimeSeriesHV.py $BUILD_HOME/qc8/chanLoss/QC8_HV_monitor_UTC_start_2019-05-20_21-00-00_end_2019-05-29_23-59-59.root 3 2 -t

will plot the HV plots for the 3/2/T layer of the cosmic stand and store them in `$ELOG_PATH/DCS_Plots.root`.
You can add the bottom layer by calling:

.. code-block:: bash

    plotTimeSeriesHV.py $BUILD_HOME/qc8/chanLoss/QC8_HV_monitor_UTC_start_2019-05-20_21-00-00_end_2019-05-29_23-59-59.root 3 2 -b -u

Now both layers will be in the same TFile.
"""

def plotTimeSeriesHV(args,qc8layer):
    """
    Makes time series plots of DCS data points

    args - namespace obtained from parsing the instane of ArgumentParser in main
    layer - string, either "top" or "bot"
    """


    # Define known constants
    knownLayers = [ "Top", "Bot" ]
    knownElectrodes = []
    for idx in range(1,4):
        for layer in knownLayers:
            knownElectrodes.append("G{0}{1}".format(idx,layer))
            pass
        pass
    knownElectrodes.append("Drift")
    knownObs = [ "Imon", "Vmon", "Status" ]
    
    if qc8layer not in knownLayers:
        raise RuntimeError("Layer '{0}' not understood, known values are {1}".format(qc8layer,knownLayers))

    # Try to load all histograms
    # ===================================================
    cName = "Chamber{0}_{1}_{2}".format(args.row,args.column,qc8layer)
    from gempython.gemplotting.utils.anautilities import getCyclicColor
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_dcsPlots = ndict() # ["Electrode"]["Obs"] = TObject
    dict_legend = {} # [Obs] = TLegend
    for idx,electrode in enumerate(knownElectrodes):
        for obsData in knownObs:
            dirName = "{0}/Channel{1}".format(cName,electrode)
            plotName= "HV_{0}{1}_{2}_UTC_time".format(obsData,cName,electrode)
            try:
                dict_dcsPlots[electrode][obsData] = inF.Get("{0}/{1}".format(dirName,plotName))
                if args.debug:
                    print("Loaded plot: {0}/{1}".format(dirName,plotName))
            except AttributeError as error:
                printYellow("Distribution '{0}' not found in input file {1}. Skipping this distribution".format(
                    plotName,
                    args.inputfile))
                continue
            dict_dcsPlots[electrode][obsData].SetLineColor(getCyclicColor(idx))
            dict_dcsPlots[electrode][obsData].SetMarkerColor(getCyclicColor(idx))
            if obsData == "Vmon" or obsData == "Status":
                dict_dcsPlots[electrode][obsData].GetYaxis().SetRangeUser(0,1e3)
                if obsData == "Vmon":
                    dict_dcsPlots[electrode][obsData].GetYaxis().SetTitle("Vmon #left(V #right)")
            elif obsData == "Imon":
                dict_dcsPlots[electrode][obsData].GetYaxis().SetRangeUser(-2,2)
                dict_dcsPlots[electrode][obsData].GetYaxis().SetTitle("Imon #left(uA #right)")

            if obsData in dict_legend.keys():
                dict_legend[obsData].AddEntry(dict_dcsPlots[electrode][obsData],electrode,"LPE")
            else:
                dict_legend[obsData] = r.TLegend(0.7,0.75,0.9,0.9)
                dict_legend[obsData].AddEntry(dict_dcsPlots[electrode][obsData],electrode,"LPE")
            pass
        pass

    # Make output TCanvas objects - All Electrodes on one TCanvas per Observable
    # ===================================================
    dict_dcsCanvas = {} # ["Obs"] = TObject
    for obsData in knownObs:
        dict_dcsCanvas[obsData] = r.TCanvas("canv_{0}_{1}".format(obsData,cName),"{0}: {1}".format(cName,obsData),900,900)
        pass

    # Draw the observable onto the corresponding canvas
    for obsData in knownObs:
        drawOpt = None
        dict_dcsCanvas[obsData].cd()
        for electrode in knownElectrodes:
            if drawOpt is None:
                dict_dcsPlots[electrode][obsData].Draw("ALPE1")
                drawOpt = "sameLPE1"
            else:
                dict_dcsPlots[electrode][obsData].Draw(drawOpt)
                pass
            pass
        dict_legend[obsData].Draw("same")
        pass

    # Make output TCanvas objects - All observables on one TCanvas per Electrode
    # ===================================================
    dict_electrodeCanvas = {} # ["Electrode"] = TObject
    for electrode in knownElectrodes:
        dict_electrodeCanvas[electrode] = r.TCanvas("canv_{0}_{1}".format(electrode,cName),"{0}: {1}".format(cName,electrode),900,1800)
        dict_electrodeCanvas[electrode].Divide(1,3)

    # Draw the observable onto the corresponding canvas
    for electrode in knownElectrodes:
        for idx,obsData in enumerate(knownObs):
            dict_electrodeCanvas[electrode].cd(idx+1)
            dict_dcsPlots[electrode][obsData].Draw("ALPE1")
            pass
        pass

    # Make output TCanvas Objects - All electrodes and all observables on one TCanvas
    # ===================================================
    canv_Summary = r.TCanvas("canv_Summary_{0}".format(cName),"{0}: Summary".format(cName), 900,1800)
    canv_Summary.Divide(1,3)

    # Draw the observable onto the corresponding canvas
    for idx,obsData in enumerate(knownObs):
        drawOpt = None
        canv_Summary.cd(idx+1)
        for electrode in knownElectrodes:
            if drawOpt is None:
                dict_dcsPlots[electrode][obsData].Draw("ALPE1")
                drawOpt = "sameLPE1"
            else:
                dict_dcsPlots[electrode][obsData].Draw(drawOpt)
                pass
            pass
        dict_legend[obsData].Draw("same")
        pass

    # Make an output TFile
    # ===================================================
    if args.update:
        rootOpt = "UPDATE"
    else:
        rootOpt = "RECREATE"

    from gempython.gemplotting.utils.anautilities import getElogPath
    elogPath = getElogPath()
    if args.outfilename is None:
        outF = r.TFile("{0}/DCS_Plots.root".format(elogPath),rootOpt)
    else:
        outF = r.TFile(args.outfilename,rootOpt)
        pass

    #thisDir = outF.mkdir(cName)
    outF.mkdir(cName)
    thisDir = outF.GetDirectory(cName)
    thisDir.cd()
    canv_Summary.Write()
    canv_Summary.SaveAs("{0}/{1}.png".format(elogPath,canv_Summary.GetName()))
    for obsData in knownObs:
        dict_dcsCanvas[obsData].Write()
        dict_dcsCanvas[obsData].SaveAs("{0}/{1}.png".format(elogPath,dict_dcsCanvas[obsData].GetName()))
        pass

    for electrode in knownElectrodes:
        dict_electrodeCanvas[electrode].Write()
        dict_electrodeCanvas[electrode].SaveAs("{0}/{1}.png".format(elogPath,dict_electrodeCanvas[electrode].GetName()))
        pass
    
    return

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Arguments to supply to plotTimeSeriesHV.py")

    parser.add_argument("inputfile", type=str, help="TFile containing DCS output files")
    parser.add_argument("row", type=int, help="Row of QC8 stand")
    parser.add_argument("column", type=int, help="Column of QC8 stand")

    qc8StandLayer = parser.add_mutually_exclusive_group(required=True)
    qc8StandLayer.add_argument("-a","--allLayers",action="store_true",help="Both stand layers")
    qc8StandLayer.add_argument("-t","--top",action="store_true",help="Stand Layer is TOP")
    qc8StandLayer.add_argument("-b","--bot",action="store_true",help="Stand Layer is BOT")
   
    parser.add_argument("-d","--debug",action="store_true",help="Prints additional debugging info")
    parser.add_argument("-o","--outfilename", type=str, help="output name of TFile", default=None)
    parser.add_argument("-u","--update", action="store_true", help="Instead of overwriting a pre-existing output file, adding this option will simply update that file")

    # Parser the arguments
    args = parser.parse_args()

    # Load the input file
    import ROOT as r
    inF = r.TFile(args.inputfile,"READ")

    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    # Check if file loaded okay
    from gempython.utils.gemlogger import colors, printGreen, printRed, printYellow
    import os
    if not inF.IsOpen() or inF.IsZombie():
        printRed("File {0} did not load properly, exiting".format(args.inputfile))
        exit(os.EX_IOERR)
        pass

    # Determine layer
    if args.allLayers:
        plotTimeSeriesHV(args,"Top")
        args.update=True
        plotTimeSeriesHV(args,"Bot")
    elif args.bot:
        plotTimeSeriesHV(args,"Bot")
    elif args.top:
        plotTimeSeriesHV(args,"Top")
        pass

    print("Goodbye")
