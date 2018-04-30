#!/bin/env python

def getStringNoSpecials(inputStr):
    """
    returns a string without special characters
    """

    inputStr = inputStr.replace('*','')
    inputStr = inputStr.replace('-','')
    inputStr = inputStr.replace('+','')
    inputStr = inputStr.replace('(','')
    inputStr = inputStr.replace(')','')
    inputStr = inputStr.replace('/','')
    inputStr = inputStr.replace('{','')
    inputStr = inputStr.replace('}','')
    inputStr = inputStr.replace('#','')

    return inputStr

def getPlotFromTree(filename, treeName, expression, selection=""):
    """
    Returns the type of TObject returned by TTree::Draw(expression, selection, drawOpt)

    filename - string, physical filename of the input TFile
    treeName - string, name of the TTree found in filename

    See https://root.cern.ch/doc/master/classTTree.html#a73450649dc6e54b5b94516c468523e45 for TTree::Draw() documentation

    expression - string, the "varexp" argument passed to TTree::Draw()
    selection - string, the "selection" argument passed to TTree::Draw()
    """
  
    import gempython.gemplotting as gemplotting
    
    from gemplotting.anautilities import filePathExists, getDirByAnaType

    import os
    import ROOT as r

    # Check input file
    if not filePathExists(filename):
        print 'getPlotFromTree() - Filepath %s does not exist!'%(filename)
        print 'getPlotFromTree() - Please cross-check, exiting!'
        exit(os.EX_DATAERR)

    # Get TTree
    try:
        dataFile = r.TFile(filename, "READ")
        dataTree = dataFile.Get(treeName)
        knownBranches = dataTree.GetListOfBranches()
    except Exception as e:
        print 'getPlotFromTree() - %s may not exist in %s, please cross check'%(treeName,filename)
        print e
        #exit(os.EX_NOTFOUND) #Weird, not found but described in: https://docs.python.org/2/library/os.html#process-management
        exit(os.EX_DATAERR)
        pass

    # Make the name for the plot
    listParsedExpress = expression.split(":")
    if len(listParsedExpress) > 2:
        print("getPlotFromTree() - Sorry right now I cannot handle N_Dimensions > 2")
        print("\tYou'll need to make your plot by hand")
        print("\tExiting")
        exit(os.EX_USAGE)

    dictPrefix = { 1:"h", 2:"g", 3:"poly3D"}
    strPlotName = dictPrefix[len(listParsedExpress)]
    for idx in range(len(listParsedExpress)-1,-1,-1):
        strPlotName = "%s_%s"%(strPlotName, getStringNoSpecials(listParsedExpress[idx]))
        if idx > 0:
            strPlotName = "%s_vs"%(strPlotName)

    # Draw the PLot
    try:
        dataTree.Draw(expression, selection)
    except Exception as e:
        print("getPlotFromTree() - An Exception has occurred, TTree::Draw() was not successful")
        print("\texpression = %s"%expression)
        print("\tselection = %s"%selection)
        print("\tdrawOpt = %s"%drawOpt)
        print("")
        print("\tMaybe you mispelled the TBranch names?")
        print("\tExisting Branches are:")
        for realBranch in knownBranches:
            print("\t",realBranch)
        print("")
        print("getPlotFromTree() - Please cross check and try again")
        print("")
        print(e)
        #exit(os.EX_NOTFOUND) #Weird, not found but described in: https://docs.python.org/2/library/os.html#process-management
        exit(os.EX_DATAERR)

    # Get the plot and return it to the user
    if len(listParsedExpress) == 1:
        #thisPlot = r.gPad.GetPrimitive("htemp").Clone(strPlotName) #For some reason if trying this I get a null pointer later :-/
        thisPlot = r.TGraph(r.gPad.GetPrimitive("htemp"))
        thisPlot.SetName(strPlotName.replace('h_','g_'))

        return thisPlot
    elif len(listParsedExpress) == 2:
        thisPlot = r.gPad.GetPrimitive("Graph").Clone(strPlotName)
        return thisPlot

if __name__ == '__main__':
    from gempython.gemplotting.anaInfo import tree_names
    from gempython.gemplotting.anautilities import filePathExists, getDirByAnaType
    from gempython.utils.wrappers import envCheck
    from gempython.gemplotting.macros.plotoptions import parser
    
    import array
    import os
    import ROOT as r
    
    parser.add_option("--anaType", type="string", dest="anaType",
                    help="Analysis type to be executed, from list {'latency','scurve','scurveAna','threshold','trim','trimAna'}", metavar="anaType")
    parser.add_option("--axisMaxX", type="float", dest="axisMaxX", default=None,
                    help="Maximum value for X-axis range", metavar="axisMaxX")
    parser.add_option("--axisMinX", type="float", dest="axisMinX", default=None,
                    help="Minimum value for X-axis range", metavar="axisMinX")
    parser.add_option("--axisMaxY", type="float", dest="axisMaxY", default=None,
                    help="Maximum value for Y-axis range", metavar="axisMaxY")
    parser.add_option("--axisMinY", type="float", dest="axisMinY", default=None,
                    help="Minimum value for Y-axis range", metavar="axisMinY")
    parser.add_option("--drawLeg", action="store_true", dest="drawLeg",
                    help="When used with --summary option draws a TLegend on the output plot", metavar="drawLeg")
    parser.add_option("--fitFunc", type="string", dest="fitFunc", default=None,
                    help="Fit function to be applied to all plots", metavar="fitFunc")
    parser.add_option("--fitGuess", type="string", dest="fitGuess", default=None,
                    help="Initial guess for params defined in --fitFunc, note the order of params here should match that of --fitFunc", metavar="fitGuess")
    parser.add_option("--fitOpt", type="string", dest="fitOpt", default="QR",
                    help="Option to be used for fitting", metavar="fitOpt")
    parser.add_option("--fitRange", type="string", dest="fitRange", default=None,
                    help="Comma separated pair of floats which define the range the fit function is valid on", metavar="fitRange")
    parser.add_option("--rootOpt", type="string", dest="rootOpt", default="RECREATE",
                    help="Option for the output TFile, e.g. {'RECREATE','UPDATE'}", metavar="rootOpt")
    parser.add_option("--showStat", action="store_true", dest="showStat",
                    help="Draws the statistics box", metavar="showStat")
    parser.add_option("--summary", action="store_true", dest="summary",
                    help="Make a summary canvas with all created plots drawn on it", metavar="summary")
    parser.add_option("--treeExpress", type="string", dest="treeExpress", default=None,
                    help="Expression to be drawn by the TTree::Draw() method", metavar="treeExpress")
    parser.add_option("--treeSel", type="string", dest="treeSel", default="",
                    help="Selection to be used by the TTree::Draw() method", metavar="treeSel")
    parser.add_option("--treeDrawOpt", type="string", dest="treeDrawOpt", default="",
                    help="Draw option to be used for the procued plots", metavar="treeDrawOpt")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                    help="Specify the p value of the trim", metavar="ztrim")
    
    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()
  
    # Check Paths
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath  = os.getenv('ELOG_PATH')

    if options.treeExpress is None:
        print("You must specify an expression to be draw with the --treeExpress option")
        print("Exiting")
        exit(os.EX_USAGE)
    
    # Check anaType is understood
    if options.anaType not in tree_names.keys():
        print("Invalid analysis specificed, please select only from the list:")
        print(tree_names.keys())
        exit(os.EX_USAGE)
        pass
    
    # Check input file
    try:
        fileScanDates = open(options.filename, 'r') #tab '\t' delimited file, first line column headings, subsequent lines data: cName\tscandate\tindepvar
    except Exception as e:
        print '%s does not seem to exist'%(options.filename)
        print e
        exit(os.EX_NOINPUT)
        pass
    
    # Make output TFile
    listParsedExpress = options.treeExpress.split(":")
    strRootName = ""
    for idx in range(len(listParsedExpress)-1,-1,-1):
        strRootName = "%s_%s"%(strRootName, getStringNoSpecials(listParsedExpress[idx]))
        if idx > 0:
            strRootName = "%s_vs"%(strRootName)
    
    strRootName = elogPath + "/gemTreeDrawWrapper%s.root"%(strRootName)
    r.gROOT.SetBatch(True)
    outF = r.TFile(strRootName,options.rootOpt)
    
    # Loop Over inputs
    listPlots = []
    for i,line in enumerate(fileScanDates):
        if line[0] == "#":
            continue

        # On 1st iteration get independent variable name
        if i == 0:
            continue
        
        # Split the line
        line = line.strip('\n')
        chamberAndScanDatePair = line.rsplit('\t') #chamber name, scandate
        if len(chamberAndScanDatePair) != 2:
            print "Input format incorrect"
            print "I was expecting a tab-delimited file with each line having 2 entries"
            print "But I received:"
            print "\t%s"%(line)
            print "Exiting"
            exit(os.EX_USAGE)

        # Setup the path
        dirPath = getDirByAnaType(options.anaType.strip("Ana"), chamberAndScanDatePair[0], options.ztrim)
        if not filePathExists(dirPath, chamberAndScanDatePair[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, scandate)
            print 'Please cross-check, exiting!'
            outF.Close()
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, chamberAndScanDatePair[1], tree_names[options.anaType][0])
        treeName = tree_names[options.anaType][1]

        # Get the Plot and Reset it's Name
        thisPlot = getPlotFromTree(filename, treeName, options.treeExpress, options.treeSel)
        strPlotName = thisPlot.GetName()
        strPlotName = "%s_%s_%s"%(strPlotName, chamberAndScanDatePair[0], chamberAndScanDatePair[1])
        thisPlot.SetName(strPlotName)
        
        # Set the Plot Title
        if options.treeSel is not None:
            thisPlot.SetTitle("#splitline{%s: %s}{%s}"%(chamberAndScanDatePair[0], chamberAndScanDatePair[1], options.treeSel))
        else:
            thisPlot.SetTitle("%s: %s"%(chamberAndScanDatePair[0], chamberAndScanDatePair[1]))

        # Set the Stat Box Options
        if options.showStat:
            r.gStyle.SetOptStat(1111111)
        else:
            r.gStyle.SetOptStat(0000000)
        
        # Make the canvas name
        strCanvName = "canv"
        strCanvTitle = getStringNoSpecials(listParsedExpress[len(listParsedExpress)-1])
        for idx in range(len(listParsedExpress)-1,-1,-1):
            strCanvName = "%s_%s"%(strCanvName, getStringNoSpecials(listParsedExpress[idx]))
            if idx > 0:
                strCanvName = "%s_vs"%(strCanvName)
                strCanvTitle = "%s vs %s"%(strCanvTitle, getStringNoSpecials(listParsedExpress[idx]))
            elif idx == 0 and len(listParsedExpress) > 1:
                strCanvTitle = "%s vs %s"%(strCanvTitle, getStringNoSpecials(listParsedExpress[idx]))
        strCanvName = "%s_%s_%s"%(strCanvName, chamberAndScanDatePair[0], chamberAndScanDatePair[1])
        strCanvTitle = "%s %s: %s"%(chamberAndScanDatePair[0], chamberAndScanDatePair[1], strCanvTitle)

        # Make the axis labels
        strAxisLabel_X = getStringNoSpecials(listParsedExpress[0])
        strAxisLabel_Y = "N"
        if len(listParsedExpress) == 2:
            strAxisLabel_Y = getStringNoSpecials(listParsedExpress[0])
            strAxisLabel_X = getStringNoSpecials(listParsedExpress[1])

        # Draw this plot on a canvas
        canvPlot = r.TCanvas(strCanvName,strCanvTitle,600,600)
        canvPlot.cd()
        thisPlot.SetMarkerStyle(22)
        thisPlot.Draw(options.treeDrawOpt)
        if options.axisMaxX is not None:
            if options.axisMinX is not None:
                thisPlot.GetXaxis().SetRangeUser(options.axisMinX, options.axisMaxX)
            else:
                thisPlot.GetXaxis().SetRangeUser(0, options.axisMaxX)
        thisPlot.GetXaxis().SetTitle(strAxisLabel_X)
        thisPlot.GetYaxis().SetDecimals(True)
        if options.axisMaxY is not None:
            if options.axisMinY is not None:
                thisPlot.GetYaxis().SetRangeUser(options.axisMinY, options.axisMaxY)
            else:
                thisPlot.GetYaxis().SetRangeUser(0, options.axisMaxY)
        thisPlot.GetYaxis().SetTitle(strAxisLabel_Y)
        thisPlot.GetYaxis().SetTitleOffset(1.2)
        canvPlot.Update()

        # Fit the plot
        if options.fitFunc is not None:
            # Do we also have a fitRange?
            if options.fitRange is None:
                print("You must specify --fitRange when using --fitFunc")
                print("Exiting")
                exit(os.EX_USAGE)

            # Make the fit name
            strFitName = "fit"
            for idx in range(len(listParsedExpress)-1,-1,-1):
                strFitName = "%s_%s"%(strFitName, getStringNoSpecials(listParsedExpress[idx]))
                if idx > 0:
                    strFitName = "%s_vs"%(strFitName)
            strFitName = "%s_%s_%s"%(strFitName, chamberAndScanDatePair[0], chamberAndScanDatePair[1])

            # Initialize the fit
            fitRange = map(lambda val: float(val), options.fitRange.split(","))
            thisFit = r.TF1(strFitName, options.fitFunc, min(fitRange), max(fitRange))

            # Set Initial Guess
            if options.fitGuess is not None:
                listParams = map(lambda val: float(val), options.fitGuess.split(","))

                if len(listParams) == thisFit.GetNpar():
                    for i,param in enumerate(listParams):
                        thisFit.SetParameter(i,param)
                else:
                    print "You must supply an initial guess for each parameter"
                    print "The initial guess values give:", listParams
                    print "Which has length %i, but I am expecting %i guesses"%(len(listParams), thisFit.GetNpar())
                    print "Exiting"
                    exit(os.EX_USAGE)

            # Perform the fit
            thisPlot.Fit(thisFit,options.fitOpt)

            # Draw the fit
            canvPlot.cd()
            thisFit.Draw("same")
            canvPlot.Update()

            # Store the fit
            outF.cd()
            thisFit.Write()

        # Save Plot and Canvas
        outF.cd()
        thisPlot.Write()
        canvPlot.SaveAs("%s/%s.png"%(elogPath,strCanvName))
        canvPlot.Write()
        listPlots.append((thisPlot, chamberAndScanDatePair[0], chamberAndScanDatePair[1]) )

    # Make Summary Plot
    if options.summary:
        # Make the canvas name
        strCanvName = "canv"
        strCanvTitle = getStringNoSpecials(listParsedExpress[len(listParsedExpress)-1])
        for idx in range(len(listParsedExpress)-1,-1,-1):
            strCanvName = "%s_%s"%(strCanvName, getStringNoSpecials(listParsedExpress[idx]))
            if idx > 0:
                strCanvName = "%s_vs"%(strCanvName)
                strCanvTitle = "%s vs %s"%(strCanvTitle, getStringNoSpecials(listParsedExpress[idx]))
            elif idx == 0 and len(listParsedExpress) > 1:
                strCanvTitle = "%s vs %s"%(strCanvTitle, getStringNoSpecials(listParsedExpress[idx]))
        
        # Make the canvas
        canvSummary = r.TCanvas("summary_%s"%strCanvName, "Summary: %s"%(strCanvTitle), 600, 600)

        # Make the Legend
        legSummary = r.TLegend(0.55,0.65,0.9,0.9)

        # Loop over plots
        for i,plotTuple in enumerate(listPlots):
            # Format the plot
            plotTuple[0].SetTitle("")
            plotTuple[0].SetMarkerStyle(20+i)
            plotTuple[0].SetMarkerColor(r.kRed-3+i)
            plotTuple[0].SetLineColor(r.kRed-3+i)
        
            # Add to the Legend
            legSummary.AddEntry(plotTuple[0],"%s: %s"%(plotTuple[1],plotTuple[2]), "LPE")

            # Draw the plot
            canvSummary.cd()
            if i == 0:
                plotTuple[0].Draw(options.treeDrawOpt)
            else:
                plotTuple[0].Draw("same%s"%options.treeDrawOpt.replace("A",""))
            
        # Draw the Legend
        if options.drawLeg:
            legSummary.Draw("same")

        # Draw the selection
        if options.treeSel is not None:
            selLatex = r.TLatex()
            selLatex.SetTextSize(0.03)
            selLatex.DrawLatexNDC(0.2,0.8,options.treeSel)

        # Save the Canvas
        outF.cd()
        canvSummary.SaveAs("%s/summary_%s.png"%(elogPath,strCanvName))
        canvSummary.Write()

    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
