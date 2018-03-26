#!/bin/env python

if __name__ == '__main__':
    from anaInfo import tree_names
    from anautilities import filePathExists, getDirByAnaType, parseListOfScanDatesFile
    from gempython.utils.wrappers import envCheck, runCommand
    from macros.plotoptions import parser
    from macros.scurvePlottingUtitilities import overlay_scurve
   
    import os
    import ROOT as r

    parser.add_option("--anaType", type="string", dest="anaType",
                    help="Analysis type to be executed, from list {'scurveAna','trimAna'}", metavar="anaType")
    parser.add_option("--drawLeg", action="store_true", dest="drawLeg",
                    help="When used with --summary option draws a TLegend on the output plot", metavar="drawLeg")
    parser.add_option("--rootOpt", type="string", dest="rootOpt", default="RECREATE",
                    help="Option for the output TFile, e.g. {'RECREATE','UPDATE'}", metavar="rootOpt")
    parser.add_option("--summary", action="store_true", dest="summary",
                    help="Make a summary canvas with all created plots drawn on it", metavar="summary")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                    help="Specify the p value of the trim", metavar="ztrim")
    
    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()
  
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
    parsedTuple = parseListOfScanDatesFile(options.filename)
    listChamberAndScanDate = parsedTuple[0]
    
    # Make output TFile
    strRootName = elogPath + "/gemSCurveAnaToolkit.root"
    r.gROOT.SetBatch(True)
    outF = r.TFile(strRootName,options.rootOpt)
    
    # Loop Over inputs
    dictPlots = {}
    for chamberAndScanDatePair in listChamberAndScanDate:
        tupleChamberAndScanDate = (chamberAndScanDatePair[0],chamberAndScanDatePair[1])

        # Setup the path
        dirPath = getDirByAnaType(options.anaType.strip("Ana"), chamberAndScanDatePair[0], options.ztrim)
        if not filePathExists(dirPath, chamberAndScanDatePair[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, scandate)
            print 'Please cross-check, exiting!'
            outF.Close()
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, chamberAndScanDatePair[1], tree_names[options.anaType][0])
   
        # Get the Plot and Reset it's Name
        dictPlots[tupleChamberAndScanDate]=overlay_scurve(
                vfat=options.vfat,
                vfatCH=options.strip,
                fit_filename=filename,
                vfatChNotROBstr=options.channels
                )

        # Rename the image of the canvas
        strChanOrStrip = "Chan"
        if not options.channels:
            strChanOrStrip = "Strip"
        cmd = ["mv"]
        cmd.append("canv_SCurveFitOverlay_VFAT%i_%s%i.png"%(
            options.vfat,
            strChanOrStrip,
            options.strip)
            )
        cmd.append("canv_SCurveFitOverlay_%s_%s_VFAT%i_%s%i.png"%(
            tupleChamberAndScanDate[0],
            tupleChamberAndScanDate[1],
            options.vfat,
            strChanOrStrip,
            options.strip)
            )
        runCommand(cmd)
        print "eog %s"%(cmd[2])

        # Save Plot
        outF.cd()
        outDir = outF.mkdir("%s_%s"%(chamberAndScanDatePair[0],chamberAndScanDatePair[1]))
        outDir.cd()
        dictPlots[tupleChamberAndScanDate][0].SetName(
                "%s_%s_%s"%(
                    dictPlots[tupleChamberAndScanDate][0].GetName(),
                    tupleChamberAndScanDate[0],
                    tupleChamberAndScanDate[1])
                )
        dictPlots[tupleChamberAndScanDate][0].Write()
        dictPlots[tupleChamberAndScanDate][1].SetName(
                "%s_%s_%s"%(
                    dictPlots[tupleChamberAndScanDate][1].GetName(),
                    tupleChamberAndScanDate[0],
                    tupleChamberAndScanDate[1])
                )
        dictPlots[tupleChamberAndScanDate][1].Write()
   
    # Make Summary Plot
    if options.summary:
        # Make the canvas
        canvSummary = r.TCanvas("summary_gemSCurveAnaToolkit", "Summary: gemSCurveAnaToolkit", 700, 700)
        canvSummary.cd().SetGridy()

        # Make the Legend
        legSummary = r.TLegend(0.1,0.65,0.45,0.9)

        # Loop over plots
        for i,keyPair in enumerate(dictPlots.keys()):
            # Format the histo
            dictPlots[keyPair][0].SetStats(False)
            dictPlots[keyPair][0].SetTitle("")
            dictPlots[keyPair][0].SetMarkerStyle(20+i)
            dictPlots[keyPair][0].SetMarkerColor(r.kRed-3+i)
            dictPlots[keyPair][0].SetLineColor(r.kRed-3+i)
        
            # Format the func
            dictPlots[keyPair][1].SetTitle("")
            dictPlots[keyPair][1].SetMarkerStyle(20+i)
            dictPlots[keyPair][1].SetMarkerColor(r.kRed-3+i)
            dictPlots[keyPair][1].SetLineColor(r.kRed-3+i)

            # Add to the Legend
            legSummary.AddEntry(dictPlots[keyPair][0],"%s: %s"%(keyPair[0],keyPair[1]), "LPE")

            # Draw the plot
            canvSummary.cd()
            if i == 0:
                dictPlots[keyPair][0].Draw()
                dictPlots[keyPair][1].Draw("same")
            else:
                dictPlots[keyPair][0].Draw("same")
                dictPlots[keyPair][1].Draw("same")
            
        # Draw the Legend
        if options.drawLeg:
            legSummary.Draw("same")

        # Save the Canvas
        outF.cd()
        canvSummary.SaveAs("%s/summary_gemSCurveAnaToolkit.png"%(elogPath))
        canvSummary.Write()

    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
