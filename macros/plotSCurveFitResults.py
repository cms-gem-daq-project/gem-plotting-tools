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
    #   Outer key -> (chamberName,scandate) tuple
    #   Inner key -> vfat position
    dict_fitSum = ndict()
    dict_ScurveMean = ndict() # Inner key: (0,23) follows vfat #, -1 is summary over all det
    dict_ScurveSigma = ndict() 
    dict_ScurveEffPed = ndict()

    dict_ScurveMeanByiEta = ndict()
    dict_ScurveSigmaByiEta = ndict() 

    # Get the plots from all files
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType(options.anaType.strip("Ana"), chamberAndScanDatePair[0], options.ztrim)
        if not filePathExists(dirPath, chamberAndScanDatePair[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, chamberAndScanDatePair[1])
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
            dict_fitSum[chamberAndScanDatePair][vfat] = scanFile.Get("VFAT%i/gFitSummary_VFAT%i"%(vfat,vfat))
            dict_fitSum[chamberAndScanDatePair][vfat].SetName(
                    "%s_%s_%s"%(
                        dict_fitSum[chamberAndScanDatePair][vfat].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_fitSum[chamberAndScanDatePair][vfat].SetLineColor(getCyclicColor(idx))
            dict_fitSum[chamberAndScanDatePair][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_fitSum[chamberAndScanDatePair][vfat].SetMarkerStyle(20+idx)

            # Scurve Mean
            dict_ScurveMean[chamberAndScanDatePair][vfat] = scanFile.Get("VFAT%i/gScurveMeanDist_vfat%i"%(vfat,vfat))
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetName(
                    "%s_%s_%s"%(
                        dict_ScurveMean[chamberAndScanDatePair][vfat].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetLineColor(getCyclicColor(idx))
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveMean[chamberAndScanDatePair][vfat].SetMarkerStyle(20+idx)
            
            # Scurve Width
            dict_ScurveSigma[chamberAndScanDatePair][vfat] = scanFile.Get("VFAT%i/gScurveSigmaDist_vfat%i"%(vfat,vfat))
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetName(
                    "%s_%s_%s"%(
                        dict_ScurveSigma[chamberAndScanDatePair][vfat].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetLineColor(getCyclicColor(idx))
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveSigma[chamberAndScanDatePair][vfat].SetMarkerStyle(20+idx)

            pass

        for ieta in range(1,9):
            # Scurve Mean
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta] = scanFile.Get("Summary/ieta%i/gScurveMeanDist_ieta%i"%(ieta,ieta))
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetName(
                    "%s_%s_%s"%(
                        dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                    )
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetLineColor(getCyclicColor(idx))
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetMarkerColor(getCyclicColor(idx))
            dict_ScurveMeanByiEta[chamberAndScanDatePair][ieta].SetMarkerStyle(20+idx)

            # Scurve Sigma
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta] = scanFile.Get("Summary/ieta%i/gScurveSigmaDist_ieta%i"%(ieta,ieta))
            dict_ScurveSigmaByiEta[chamberAndScanDatePair][ieta].SetName(
                    "%s_%s_%s"%(
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
                    "%s_%s_%s"%(
                        dict_ScurveMean[chamberAndScanDatePair][-1].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        dict_ScurveMean[chamberAndScanDatePair][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveMean[chamberAndScanDatePair][-1].SetMarkerColor(getCyclicColor(idx))
        dict_ScurveMean[chamberAndScanDatePair][-1].SetMarkerStyle(20+idx)

        dict_ScurveSigma[chamberAndScanDatePair][-1] = scanFile.Get("Summary/gScurveSigmaDist_All")
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetName(
                    "%s_%s_%s"%(
                        dict_ScurveSigma[chamberAndScanDatePair][-1].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetMarkerColor(getCyclicColor(idx))
        dict_ScurveSigma[chamberAndScanDatePair][-1].SetMarkerStyle(20+idx)
        
        dict_ScurveEffPed[chamberAndScanDatePair][-1] = scanFile.Get("Summary/hScurveEffPedDist_All")
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetName(
                    "%s_%s_%s"%(
                        dict_ScurveEffPed[chamberAndScanDatePair][-1].GetName(),
                        chamberAndScanDatePair[0],
                        chamberAndScanDatePair[1])
                )
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetLineColor(getCyclicColor(idx))
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetMarkerColor(getCyclicColor(idx))
        dict_ScurveEffPed[chamberAndScanDatePair][-1].SetMarkerStyle(20+idx)
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
    plotLeg = r.TLegend(0.1,0.65,0.45,0.9)
    for idx,chamberAndScanDatePair in enumerate(listChamberAndScanDate):
        drawOpt="APE1"

        # Draw per VFAT distributions
        for vfat in range(0,24):
            if idx == 0:
                dict_mGraph_fitSum[vfat]    = r.TMultiGraph("mGraph_FitSummary_VFAT%i"%(vfat),"VFAT%i"%(vfat))
                dict_mGraph_ScurveMean[vfat]= r.TMultiGraph("mGraph_ScurveMeanDist_vfat%i"%(vfat),"VFAT%i"%(vfat))
                dict_mGraph_ScurveSigma[vfat]=r.TMultiGraph("mGraph_ScurveSigmaDist_vfat%i"%(vfat),"VFAT%i"%(vfat))

                dict_canvSCurveFitSum[vfat] = r.TCanvas("canvScurveFitSum_VFAT%i"%(vfat),"SCurve Fit Summary - VFAT%i"%(vfat),600,600)
                dict_canvSCurveMean[vfat]   = r.TCanvas("canvScurveMean_VFAT%i"%(vfat),"SCurve Mean - VFAT%i"%(vfat),600,600)
                dict_canvSCurveSigma[vfat]  = r.TCanvas("canvScurveSigma_VFAT%i"%(vfat),"SCurve Sigma - VFAT%i"%(vfat),600,600)
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
        for ieta in range(1,9):
            if idx == 0:
                dict_mGraph_ScurveMeanByiEta[ieta] = r.TMultiGraph("mGraph_ScurveMeanDist_ieta%i"%(ieta),"i#eta = %i"%(ieta))
                dict_mGraph_ScurveSigmaByiEta[ieta] = r.TMultiGraph("mGraph_ScurveSigmaDist_ieta%i"%(ieta),"i#eta = %i"%(ieta))

                dict_canvSCurveMeanByiEta[ieta]   = r.TCanvas("canvScurveMean_ieta%i"%(ieta),"SCurve Mean - ieta%i"%(ieta),600,600)
                dict_canvSCurveSigmaByiEta[ieta]  = r.TCanvas("canvScurveSigma_ieta%i"%(ieta),"SCurve Sigma - ieta%i"%(ieta),600,600)
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

        # Fill Legend - use VFAT0 of each
        plotLeg.AddEntry(dict_fitSum[chamberAndScanDatePair][0],chamberAndScanDatePair[2],"LPE")
        pass

    # Draw multigraphs for summary cases
    canvFitSum_Grid = make3x8Canvas("scurveFitSummaryGridAllScandates",dict_mGraph_fitSum,"APE1")
    canvScurveMean_Grid = make3x8Canvas("scurveMeanGridAllScandates",dict_mGraph_ScurveMean,"APE1")
    canvScurveSigma_Grid = make3x8Canvas("scurveSigmaGridAllScandates",dict_mGraph_ScurveSigma,"APE1")

    canvScurveMean_Grid_iEta = make2x4Canvas("scurveMeanGridByiEtaAllScandates",dict_mGraph_ScurveMeanByiEta,"APE1")
    canvScurveSigma_Grid_iEta = make2x4Canvas("scurveSigmaGridByiEtaAllScandates",dict_mGraph_ScurveSigmaByiEta,"APE1")
    
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
        pass

    # Make output images
    canvFitSum_Grid.SaveAs("%s/%s.png"%(elogPath,canvFitSum_Grid.GetName()))
    canvScurveMean_Grid.SaveAs("%s/%s.png"%(elogPath,canvScurveMean_Grid.GetName()))
    canvScurveSigma_Grid.SaveAs("%s/%s.png"%(elogPath,canvScurveSigma_Grid.GetName()))

    canvScurveMean_Grid_iEta.SaveAs("%s/%s.png"%(elogPath,canvScurveMean_Grid_iEta.GetName()))
    canvScurveSigma_Grid_iEta.SaveAs("%s/%s.png"%(elogPath,canvScurveSigma_Grid_iEta.GetName()))
    
    canvScurveMean_DetSum.SaveAs("%s/%s.png"%(elogPath,canvScurveMean_DetSum.GetName()))
    canvScurveSigma_DetSum.SaveAs("%s/%s.png"%(elogPath,canvScurveSigma_DetSum.GetName()))
    canvScurveEffPed_DetSum.SaveAs("%s/%s.png"%(elogPath,canvScurveEffPed_DetSum.GetName()))

    # Save summary canvas objects in output root file
    outF = r.TFile("%s/%s"%(elogPath,options.rootName),options.rootOpt)
    
    for vfat in range(0,24):
        dirVFAT = outF.mkdir("VFAT%i"%(vfat))
        dirVFAT.cd()

        dict_canvSCurveFitSum[vfat].Write()
        dict_mGraph_fitSum[vfat].Write()

        dict_canvSCurveMean[vfat].Write()
        dict_mGraph_ScurveMean[vfat].Write()

        dict_canvSCurveSigma[vfat].Write()
        dict_mGraph_ScurveSigma[vfat].Write()
        pass

    dirSummary = outF.mkdir("Summary")
    for ieta in range(1,9):
        dir_iEta = dirSummary.mkdir("ieta%i"%ieta)
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

    print "Your plots can be found in:"
    print ""
    print "     %s"%elogPath
    print ""
    
    print "You can open the output TFile via:"
    print ""
    print "     root -l %s/%s"%(elogPath,options.rootName)

    print ""
    print "Good-bye"
