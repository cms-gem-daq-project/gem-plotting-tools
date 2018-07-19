#!/bin/env python

"""
calibrateThrDac.py
====================
"""

if __name__ == '__main__':
    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to sca.py')
    parser.add_argument("filename", type=str, 
            help="Tab delimited file specifying the input list of scandates, in three column format, specifying chamberName, scandate, and either CFG_THR_ARM_DAC or CFG_THR_ZCC_DAC value", 
            metavar="filename")

    parser.add_argument("--fitRange", type=str, dest="fitRange", default="0,255", 
            help="Range of 'CFG_THR_*_DAC' to use in fitting when deriving the calibration curve",
            metavar="fitRange") 
    parser.add_argument("--listOfVFATs", type=str, dest="listOfVFATs", default=None,
            help="If provided the VFATID will be taken from this file rather than scurveTree.  Tab delimited file, first line is a column header, subsequent lines specify respectively VFAT position and VFAT serial number.  Lines beginning with the '#' character will be skipped", 
            metavar="listOfVFATs")
    parser.add_argument("--noLeg", action="store_true", dest="noLeg",
            help="Do not draw a TLegend on the output plots", metavar="noLeg")
    (options, args) = parser.parse_args()

    # Suppress all pop-ups from ROOT
    r.gROOT.SetBatch(True)

    # Check Paths
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    dataPath = os.getenv('DATA_PATH')
    elogPath = os.getenv('ELOG_PATH')

    # Get info from input file
    from gempython.gemplotting.utils.anautilities import getCyclicColor, getDirByAnaType, filePathExists, parseListOfScanDatesFile, performFit
    parsedTuple = parseListOfScanDatesFile(options.filename, options.alphaLabels)
    listChamberAndScanDate = parsedTuple[0]
    thrDacName = parsedTuple[1]
    chamberName = listChamberAndScanDate[0][0]

    # Do we load an optional vfat serial number table? (e.g. chips did not have serial number in efuse burned in)
    import numpy as np
    import root_numpy as rp
    if options.listOfVFATs is not None:
        try:
            mapVFATPos2VFATSN = np.loadtxt(
                        fname = options.listOfVFATs,
                        dtype={'names':('vfatN', 'serialNum'),
                                'formats':('i4', 'i4')},
                        skiprows=1,
                    )
        except Exception as e:
            print '{0} does not seem to exist, is not readable, or does not have the right format'.format(options.listOfVFATs)
            print e
            exit(os.EX_NOINPUT)
            pass

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
    dict_ScurveSigmaVsThrDac = {}

    legArmDacValues = r.TLegend(0.6,0.6,0.9,0.9)

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
            print("Please double check your input list of scandates: {0}".format(options.filename))
            print("And then call this script again")
            raise IOError

        # Determine vfatID
        list_bNames = ['vfatN','vfatID']
        array_vfatData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)
        array_vfatData = np.unique(array_vfatData)
        
        ###################
        # Get and fit individual distributions
        ###################
        for vfat in range(-1,24):
            if vfat == -1:
                suffix = "All"
                directory = "Summary"
            else:
                if options.listOfVFATs is not None:
                    vfatID = mapVFATPos2VFATSN[mapVFATPos2VFATSN['vfatN'] == vfat]
                else:
                    if len(array_vfatData[array_vfatData['vfatN'] == vfat]) > 0:
                        vfatID = array_vfatData[array_vfatData['vfatN'] == vfat]
                    else:
                        vfatID = 0
                suffix = "vfatN{0}_vfatID{1}".format(vfat,vfatID)
                directory = suffix.upper()

            # Make the TMultiGraph Objects
            if idx == 0:
                dict_mGraphScurveMean[vfat] = r.TMultiGraph("mGraph_ScurveMeanByThrDac_{0}".format(suffix),"{0}".format(suffix))
                dict_mGraphScurvSigma[vfat] = r.TMultiGraph("mGraph_ScurveSigmaByThrDac_{0}".format(suffix),"{0}".format(suffix))

                dict_ScurveMeanVsThrDac[vfat] = r.TGraphErrors(len(listChamberAndScanDate))
                dict_ScurveMeanVsThrDac[vfat].SetName("gScurveSigma_vs_{0}_{1}".format(thrDacName,suffix))

                dict_ScurveSigmaVsThrDac[vfat] = r.TGraphErrors(len(listChamberAndScanDate))
                dict_ScurveSigmaVsThrDac[vfat].SetName("gScurveSigma_vs_{0}_{1}".format(thrDacName,suffix))

            ###################
            ### Scurve Mean ###
            ###################
            dict_gScurveMean[infoTuple[2]][vfat] = scanFile.Get("{0}/gScurveMeanDist_{0}".format(directory,suffix))

            #Set style of TGraphErrors
            dict_gScurveMean[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerStyle(21)
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Get the fitted function
            dict_funcScurveMean[infoTuple[2]][vfat] = performFit(dict_gScurveMean[infoTuple[2]][vfat])

            # Set style of TF1
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineWidth(2)
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineStyle(3)

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
            dict_gScurveSigma[infoTuple[2]][vfat] = scanFile.Get("{0}/gScurveSigmaDist_{0}".format(directory,suffix))

            #Set style of TGraphErrors
            dict_gScurveSigma[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerStyle(21)
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Get the fitted function
            dict_funcScurveSigma[infoTuple[2]][vfat] = performFit(dict_gScurveSigma[infoTuple[2]][vfat])

            # Set style of TF1
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineWidth(2)
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineStyle(3)

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

    ###################
    # Make output calibration file
    ###################
    import os
    try:
        calThrDacFile = open("{0}/{1}/calFile_{2}_{1}.txt".format(dataPath,chamberName,thrDacName))
    except IOError as e:
        print("Caught Exception: {0}".format(e))
        print("Unabled to open file '{0}/{1}/calFile_{2}_{1}.txt'".format(dataPath,chamberName,thrDacName))
        print("Perhaps the path does not exist or you do not have write permissions?")
        exit(os.EX_IOERR)
    calThrDacFile.write("vfatN/I:slope/F:intercept/F\n")

    ###################
    # Make output ROOT file
    ###################
    outFileName = "{0}/calFile_{1}_{2}.root".format(elogPath,chamberName,thrDacName)
    outFile = r.TFile(outFileName,"RECREATE")

    # Plot Containers
    dict_canvScurveMeanByThrDac = {}
    dict_canvScurveSigmaByThrDac = {}
    dict_canvScurveMeanVsThrDac = {}
    dict_canvScurveSigmaVsThrDac = {}

    ###################
    # Now Make plots - VFAT Level
    ###################
    print("vfatN\tcal_thr_m\tcal_thr_m_err\tcal_thr_b\tcal_thr_b_err\tnoise\tnoise_err")
    for vfat in range(-1,24):
        if vfat == -1:
            suffix = "All"
            directory = "Summary"
        else:
            suffix = "vfat{0}".format(vfat)
            directory = suffix.upper()

        thisDirectory = outFile.mkdir(directory)
        thisDirectory.cd()

        # Mean by CFG_THR_*_DAC
        dict_canvScurveMeanByThrDac[vfat] = r.TCanvas("canvScurveMeanByThrDac_{0}".format(suffix),"Scurve Mean by THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanByThrDac[vfat].cd()
        dict_mGraphScurveMean.Draw("APE1")
        dict_mGraphScurveMean.Write()

        # Sigma by CFG_THR_*_DAC
        dict_canvScurveSigmaByThrDac[vfat] = r.TCanvas("canvScurveSigmaByThrDac_{0}".format(suffix),"Scurve Sigma by THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaByThrDac[vfat].cd()
        dict_mGraphScurveSigma.Draw("APE1")
        dict_mGraphScurveSigma.Write()

        # Mean vs CFG_THR_*_DAC
        dict_canvScurveMeanVsThrDac[vfat] = r.TCanvas("canvScurveMeanVsThrDac_{0}".format(suffix),"Scurve Mean vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanVsThrDac[vfat].cd()
        dict_ScurveMeanVsThrDac.Draw("APE1")
        dict_ScurveMeanVsThrDac.Write()
        func_ScurveMeanVsThrDac = performFit(dict_ScurveMeanVsThrDac, formula="[0]*x+[1]")
        func_ScurveMeanVsThrDac.Write()        

        # Sigma vs CFG_THR_*_DAC
        dict_canvScurveSigmaVsThrDac[vfat] = r.TCanvas("canvScurveSigmaVsThrDac_{0}".format(suffix),"Scurve Sigma vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaVsThrDac[vfat].cd()
        dict_ScurveSigmaVsThrDac.Draw("APE1")
        dict_ScurveSigmaVsThrDac.Write()
        func_ScurveSigmaVsThrDac = performFit(dict_ScurveSigmaVsThrDac, formula="pol0")
        func_ScurveSigmaVsThrDac.Write()        

        # Write CFG_THR_*_DAC calibration file
        calThrDac.write("{0}\t{1}\t{2}\n".format(
            vfat,
            func_ScurveMeanVsThrDac.GetParameter(0),
            func_ScurveMeanVsThrDac.GetParameter(1))
            )

        # Draw Legend?
        if not options.noLeg:
            dict_canvScurveMeanByThrDac[vfat].cd()
            legArmDacValues.Draw("same")

            dict_canvScurveSigmaByThrDac[vfat].cd()
            legArmDacValues.Draw("same")

            dict_canvScurveMeanVsThrDac[vfat].cd()
            legArmDacValues.Draw("same")

            dict_canvScurveSigmaVsThrDac[vfat].cd()
            legArmDacValues.Draw("same")
            pass

        # Store Canvases
        dict_canvScurveMeanByThrDac[vfat].Write()
        dict_canvScurveSigmaByThrDac[vfat].Write()
        dict_canvScurveMeanVsThrDac[vfat].Write()
        dict_canvScurveSigmaVsThrDac[vfat].Write()

        # Print info to user
        print("vfatN\tcal_thr_m\tcal_thr_m_err\tcal_thr_b\tcal_thr_b_err\tnoise\tnoise_err")
        print("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(
            vfat,
            func_ScurveMeanVsThrDac.GetParameter(0),
            func_ScurveMeanVsThrDac.GetParError(0),
            func_ScurveMeanVsThrDac.GetParameter(1),
            func_ScurveMeanVsThrDac.GetParError(1),
            func_ScurveSigmaVsThrDac.GetParameter(0),
            func_ScurveSigmaVsThrDac.GetParError(1))
            )

    for vfat in range(-1,24):
        dict_canvScurveMeanByThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveMeanByThrDac[vfat].GetName()))
        dict_canvScurveSigmaByThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveSigmaByThrDac[vfat].GetName()))
        dict_canvScurveMeanVsThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveMeanVsThrDac[vfat].GetName()))
        dict_canvScurveSigmaVsThrDac[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canvScurveSigmaVsThrDac[vfat].GetName()))
    
    outFile.Close()
    calThrDac.close()

    print("Your calibration file is located in:")
    print("\n\t{0}/{1}/calFile_{2}_{1}.txt\n".format(dataPath,chamberName,thrDacName))

    print("You can find all ROOT objects in:")
    print("\n\t{0}/calFile_{1}_{2}.root\n".format(elogPath,chamberName,thrDacName))

    print("You can find all plots in:")
    print("\n\t{0}\n".format(elogPath))

    print("Done")
