#!/bin/env python

if __name__ == '__main__':
    from anaInfo import tree_names
    from anautilities import getCyclicColor, getDirByAnaType, filePathExists, make2x4Canvas, make3x8Canvas, parseListOfScanDatesFile
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import envCheck, runCommand
    from macros.plotoptions import parser
    from macros.scurvePlottingUtitilities import overlay_scurve
   
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
    #   Outer key -> scandate
    #   Inner key -> vfat position
    dict_fitSum = ndict()
    dict_ScurveMean = ndict() # Inner key: (0,23) follows vfat #, -1 is summary over all det
    dict_ScurveSigma = ndict() 
   
    dict_ScurveMeanByiEta = ndict()
    dict_ScurveSigmaByiEta = ndict() 

    # Get the plots from all files
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType(options.anaType.strip("Ana"), chamberAndScanDatePair[0], options.ztrim)
        if not filePathExists(dirPath, chamberAndScanDatePair[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, scandate)
            print 'Please cross-check, exiting!'
            outF.Close()
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, chamberAndScanDatePair[1], tree_names[options.anaType][0])

        # Load the file
        r.TH1.AddDirectory(False)
        scanFile   = r.TFile(filename,"READ")

        # Get all plots from scanFile - vfat level
        for vfat in range(0,24):
            # Fit summary 
            dict_fitSum[chamberAndScanDatePair[1]][vfat] = scanFile.Get("VFAT%i/gFitSummary_VFAT%i"%(vfat,vfat))
            dict_fitSum[chamberAndScanDatePair[1]][vfat].SetName(
                    "%s_%s"%(
                        dict_fitSum[chamberAndScanDatePair[1]][vfat].GetName(),
                        chamberAndScanDatePair[1])
                    )
            dict_fitSum[chamberAndScanDatePair[1]][vfat].SetLineColor(getCyclicColor(idx))
            dict_fitSum[chamberAndScanDatePair[1]][vfat].SetMarkerColor(getCyclicColor(idx))

            # Scurve Mean
            dict_ScurveMean[chamberAndScanDatePair[1]][vfat] = scanFile.Get("VFAT%i/gScurveMeanDist_vfat%i"%(vfat,vfat))
            dict_ScurveMean[chamberAndScanDatePair[1]][vfat].SetName(
                    "%s_%s"%(
                        dict_ScurveMean[chamberAndScanDatePair[1]][vfat].GetName(),
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveMean[chamberAndScanDatePair[1]][vfat].SetLineColor(getCyclicColor(idx))
            dict_ScurveMean[chamberAndScanDatePair[1]][vfat].SetMarkerColor(getCyclicColor(idx))
            
            # Scurve Width
            dict_ScurveSigma[chamberAndScanDatePair[1]][vfat] = scanFile.Get("VFAT%i/gScurveSigmaDist_vfat%i"%(vfat,vfat))
            dict_ScurveSigma[chamberAndScanDatePair[1]][vfat].SetName(
                    "%s_%s"%(
                        dict_ScurveSigma[chamberAndScanDatePair[1]][vfat].GetName(),
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveSigma[chamberAndScanDatePair[1]][vfat].SetLineColor(getCyclicColor(idx))
            dict_ScurveSigma[chamberAndScanDatePair[1]][vfat].SetMarkerColor(getCyclicColor(idx))

            pass

        for ieta in range(1,9):
            # Scurve Mean
            dict_ScurveMeanByiEta[chamberAndScanDatePair[1]][ieta] = scanFile.Get("Summary/ieta%i/gScurveMeanDist_ieta%i"%(ieta,ieta))
            dict_ScurveMeanByiEta[chamberAndScanDatePair[1]][ieta].SetName(
                    "%s_%s"%(
                        dict_ScurveMeanByiEta[chamberAndScanDatePair[1]][ieta].GetName(),
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveMeanByiEta[chamberAndScanDatePair[1]][ieta].SetLineColor(getCyclicColor(idx))
            dict_ScurveMeanByiEta[chamberAndScanDatePair[1]][ieta].SetMarkerColor(getCyclicColor(idx))

            # Scurve Sigma
            dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]][ieta] = scanFile.Get("Summary/ieta%i/gScurveSigmaDist_ieta%i"%(ieta,ieta))
            dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]][ieta].SetName(
                    "%s_%s"%(
                        dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]][ieta].GetName(),
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]][ieta].SetLineColor(getCyclicColor(idx))
            dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]][ieta].SetMarkerColor(getCyclicColor(idx))
            pass

        # Get the detector level plots
        dict_ScurveMean[chamberAndScanDatePair[1]][-1] = scanFile.Get("Summary/gScurveMeanDist_All")
        dict_ScurveMean[chamberAndScanDatePair[1]][-1].SetName(
                    "%s_%s"%(
                        dict_ScurveMean[chamberAndScanDatePair[1]][-1].GetName(),
                        chamberAndScanDatePair[1])
                )
        dict_ScurveMean[chamberAndScanDatePair[1]][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveMean[chamberAndScanDatePair[1]][-1].SetMarkerColor(getCyclicColor(idx))

        dict_ScurveSigma[chamberAndScanDatePair[1]][-1] = scanFile.Get("Summary/gScurveMeanDist_All")
        dict_ScurveSigma[chamberAndScanDatePair[1]][-1].SetName(
                    "%s_%s"%(
                        dict_ScurveSigma[chamberAndScanDatePair[1]][-1].GetName(),
                        chamberAndScanDatePair[1])
                )
        dict_ScurveSigma[chamberAndScanDatePair[1]][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveSigma[chamberAndScanDatePair[1]][-1].SetMarkerColor(getCyclicColor(idx))
        
        pass

    # Make the plots
    dict_canvSCurveFitSum = ndict()
    dict_canvSCurveMean = ndict()
    dict_canvSCurveMeanByiEta = ndict()
    dict_canvSCurveSigma = ndict()
    dict_canvSCurveSigmaByiEta = ndict()
    
    canvFitSum_Grid = None
    canvScurveMean_DetSum = r.TCanvas("canvSCurveMeanDetSumAllScandates","Scurve Mean - Detector Summary",600,600)
    canvScurveMean_Grid = None
    canvScurveMean_Grid_iEta = None
    canvScurveSigma_DetSum = r.TCanvas("canvSCurveSigmaDetSumAllScandates","Scurve Sigma - Detector Summary",600,600)
    canvScurveSigma_Grid = None
    canvScurveSigma_Grid_iEta = None
    plotLeg = r.TLegend(0.1,0.65,0.45,0.9)
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        # Determine draw option
        if idx==0:
            drawOpt="APE1"
        else:
            drawOpt="samePE1"

        # Draw per VFAT distributions
        for vfat in range(0,24):
            if idx == 0:
                dict_canvSCurveFitSum[vfat] = r.TCanvas("canvScurveFitSum_VFAT%i"%(vfat),"SCurve Fit Summary - VFAT%i"%(vfat),600,600)
                dict_canvSCurveMean[vfat]   = r.TCanvas("canvScurveMean_VFAT%i"%(vfat),"SCurve Mean - VFAT%i"%(vfat),600,600)
                dict_canvSCurveSigma[vfat]  = r.TCanvas("canvScurveSigma_VFAT%i"%(vfat),"SCurve Sigma - VFAT%i"%(vfat),600,600)
                pass

            dict_canvSCurveFitSum[vfat].cd()
            dict_fitSum[chamberAndScanDatePair[1]][vfat].Draw(drawOpt)
            
            dict_canvSCurveMean[vfat].cd()
            dict_ScurveMean[chamberAndScanDatePair[1]][vfat].Draw(drawOpt)

            dict_canvSCurveSigma[vfat].cd()
            dict_ScurveSigma[chamberAndScanDatePair[1]][vfat].Draw(drawOpt)
            pass

        # Draw per ieta distributions
        for ieta in range(1,9):
            if idx == 1:
                dict_canvSCurveMeanByiEta[ieta]   = r.TCanvas("canvScurveMean_ieta%i"%(ieta),"SCurve Mean - ieta%i"%(ieta),600,600)
                dict_canvSCurveSigmaByiEta[ieta]  = r.TCanvas("canvScurveSigma_ieta%i"%(ieta),"SCurve Sigma - ieta%i"%(ieta),600,600)
                pass

            dict_canvSCurveMeanByiEta[ieta].cd()
            dict_ScurveMeanByiEta[chamberAndScanDatePair[1]][ieta].Draw(drawOpt)

            dict_canvSCurveSigmaByiEta[ieta].cd()
            dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]][ieta].Draw(drawOpt)
            pass

        # Draw grid distributions
        canvFitSum_Grid = make3x8Canvas("scurveFitSummaryGridAllScandates",dict_fitSum[chamberAndScanDatePair[1]],drawOpt,canv=canvFitSum_Grid)
        canvScurveMean_Grid = make3x8Canvas("scurveMeanGridAllScandates",dict_ScurveMean[chamberAndScanDatePair[1]],drawOpt,canv=canvScurveMean_Grid)
        canvScurveSigma_Grid = make3x8Canvas("scurveSigmaGridAllScandates",dict_ScurveSigma[chamberAndScanDatePair[1]],drawOpt,canv=canvScurveSigma_Grid)

        canvScurveMean_Grid_iEta = make2x4Canvas("scurveMeanGridByiEtaAllScandates",dict_ScurveMeanByiEta[chamberAndScanDatePair[1]],drawOpt,canv=canvScurveMean_Grid_iEta)
        canvScurveSigma_Grid_iEta = make2x4Canvas("scurveSigmaGridByiEtaAllScandates",dict_ScurveSigmaByiEta[chamberAndScanDatePair[1]],drawOpt,canv=canvScurveSigma_Grid_iEta)

        # Draw detector summary distributions
        canvScurveMean_DetSum.cd()
        dict_ScurveMean[chamberAndScanDatePair[1]][-1].Draw(drawOpt)
        canvScurveSigma_DetSum.cd()
        dict_ScurveSigma[chamberAndScanDatePair[1]][-1].Draw(drawOpt)

        # Fill Legend - use VFAT0 of each
        plotLeg.AddEntry(dict_fitSum[chamberAndScanDatePair[1]][0],chamberAndScanDatePair[2],"LPE")
        pass

    if options.drawLeg:
        # VFAT level
        for vfat in range(0,24):
            dict_canvSCurveFitSum[vfat].cd()
            plotLeg.Draw("same")
            
            dict_canvSCurveMean[vfat].cd()
            plotLeg.Draw("same")

            dict_canvSCurveSigma[vfat].cd()
            plotLeg.Draw("same")
            pass

        # ieta level
        for ieta in range(1,9):
            dict_canvSCurveMeanByiEta.cd()
            plotLeg.Draw("same")

            dict_canvSCurveSigmaByiEta.cd()
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
        
        canvScurveMean_DetSum.cd()
        plotLeg.Draw("same")
        
        canvScurveSigma_DetSum.cd()
        plotLeg.Draw("same")
        pass

    # Make output images
    canvFitSum_Grid.SaveAs("%s/%s.png"%(elogPath,canvFitSum_Grid.GetName()))
    canvScurveMean_Grid.SaveAs("%s/%s.png"%(elogPath,canvScurveMean_Grid.GetName()))
    canvScurveSigma_Grid.SaveAs("%s/%s.png"%(elogPath,canvScurveSigma_Grid.GetName()))

    canvScurveMean_Grid_iEta.SaveAs("%s/%s.png"%(elogPath,canvScurveMean_Grid_iEta.GetName()))
    canvScurveSigma_Grid_iEta.SaveAs("%s/%s.png"%(elogPath,canvScurveSigma_Grid_iEta.GetName()))
    
    canvScurveMean_DetSum.SaveAs("%s/%s.png"%(elogPath,canvScurveMean_DetSum.GetName()))
    canvScurveSigma_DetSum.SaveAs("%s/%s.png"%(elogPath,canvScurveSigma_DetSum.GetName()))

    # Save summary canvas objects in output root file
    outF = r.TFile("%s/%s"%(elogPath,options.rootName),options.rootOpt)
    
    for vfat in range(0,24):
        dirVFAT = outF.mkdir("VFAT%i"%(vfat))
        dirVFAT.cd()

        dict_canvSCurveFitSum[vfat].Write()
        dict_canvSCurveMean[vfat].Write()
        dict_canvSCurveSigma[vfat].Write()
        pass

    dirSummary = outF.mkdir("Summary")
    dirSummary.cd()
    for ieta in range(1,9):
        dir_iEta = dirSummary.mkdir("ieta%i"%ieta)
        dir_iEta.cd()

        dict_canvSCurveMeanByiEta[ieta].Write()
        dict_canvSCurveSigmaByiEta[ieta].Write()

    canvFitSum_Grid.Write()
    canvScurveMean_Grid.Write()
    canvScurveMean_Grid_iEta.Write()
    canvScurveSigma_Grid.Write()
    canvScurveSigma_Grid_iEta.Write()
    canvScurveMean_DetSum.Write()
    canvScurveSigma_DetSum.Write()

    print "Your plots can be found in:"
    print ""
    print "     %s"%elogPath
    print ""
    
    print "You can open the output TFile via:"
    print ""
    print "     root -l %s/%s"%(elogPath,options.rootName)

    print ""
    print "Good-bye"
