#!/bin/env python

def getStringNoSpecials(inputStr):
    """
    returns a string without special characters
    """

    inputStr = inputStr.replace('*')
    inputStr = inputStr.replace('-')
    inputStr = inputStr.replace('+')
    inputStr = inputStr.replace('(')
    inputStr = inputStr.replace(')')
    inputStr = inputStr.replace('/')

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
  
    from anautilities import filePathExists, getDirByAnaType

    import os
    import ROOT as r

    # Check input file
    if not filePathExists(filename, ""):
        print 'Filepath %s does not exist!'%(filename)
        print 'Please cross-check, exiting!'
        exit(os.EX_DATAERR)

    # Get TTree
    try:
        dataFile = r.TFile(filename, "READ")
        dataTree = dataFile.Get(treeName)
        knownBranches = dataTree.GetListOfBranches()
    except Exception as e:
        print '%s may not exist in %s, please cross check'%(treeName,filename)
        print e
        #exit(os.EX_NOTFOUND) #Weird, not found but described in: https://docs.python.org/2/library/os.html#process-management
        exit(os.EX_DATAERR)
        pass

    # Make the name for the plot
    listParsedExpress = expression.split(":")
    if len(listParsedExpress) > 2:
        print("Sorry right now I cannot handle N_Dimensions > 2")
        print("You'll need to make your plot by hand")
        print("Exiting")
        exit(os.EX_USAGE)

    dictPrefix = { 1:"h", 2:"g", 3:"poly3D"}
    strPlotName = "%s_"%dictPrefix[len(listParsedExpress)]
    for idx,item in enumerate(listParsedExpress):
        strPlotName = "%s_%s"%(strPlotName, getStringNoSpecials(item))
        if idx > 0:
            strPlotName = "%s_vs_"%(strPlotName)

    # Draw the PLot
    try:
        dataTree.Draw(expression, selection)
    except Exception as e:
        print("An Exception has occurred, TTree::Draw() was not successful")
        print("\texpression = %s"%expression)
        print("\tselection = %s"%selection)
        print("\tdrawOpt = %s"%drawOpt)
        print("")
        print("\tMaybe you mispelled the TBranch names?")
        print("\tExisting Branches are:")
        for realBranch in knownBranches:
            print("\t",realBranch)
        print("")
        print("Please cross check and try again")
        print("")
        print(e)
        #exit(os.EX_NOTFOUND) #Weird, not found but described in: https://docs.python.org/2/library/os.html#process-management
        exit(os.EX_DATAERR)

    # Get the plot and return it to the user
    if len(listParsedExpress) == 1:
        thisPlot = r.gPad.GetPrimitive("htemp").Clone(strPlotName)
        return thisPlot
    elif len(listParsedExpress) == 2:
        thisPlot = r.gPad.GetPrimitive("Graph").Clone(strPlotName)
        return thisPlot

if __name__ == '__main__':
    from anaInfo import tree_names
    from gempython.utils.wrappers import envCheck
    from macros.plotoptions import parser
    
    import array
    import os
    import ROOT as r
    
    parser.add_option("--axisMax", type="float", dest="axisMax", default=255,
                    help="Maximum value for axis depicting branchName", metavar="axisMax")
    parser.add_option("--axisMin", type="float", dest="axisMin", default=0,
                    help="Minimum value for axis depicting branchName", metavar="axisMin")
    parser.add_option("--anaType", type="string", dest="anaType",
                    help="Analysis type to be executed, from list {'latency','scurve','scurveAna','threshold','trim','trimAna'}", metavar="anaType")
    parser.add_option("--fitFunc", action="string", dest="fitFunc", default=None,
                    help="Fit function to be applied to all plots", metavar="fitFunc")
    parser.add_option("--fitOpt", action="string", dest="fitOpt", default=None,
                    help="Option to be used for fitting", metavar="fitOpt")
    parser.add_option("--fitRange", action="string", dest="fitRange", default=None,
                    help="Range the fit function is defined on", metavar="fitRange")
    #parser.add_option("-p","--print", action="store_true", dest="printData",
    #                help="Prints a comma separated table with the data to the terminal", metavar="printData")
    parser.add_option("--rootOpt", type="string", dest="rootOpt", default="RECREATE",
                    help="Option for the output TFile, e.g. {'RECREATE','UPDATE'}", metavar="rootOpt")
    parser.add_option("--showStat", action="store_true", dest="showStat",
                    help="Draws the statistics box for 2D plots", metavar="showStat")
    parser.add_option("--treeExpress", type="string", dest="treeExpress", default=None,
                    help="Expression to be drawn by the TTree::Draw() method", metavar="treeExpress")
    parser.add_option("--treeSel", type="string", dest="treeSel", default="",
                    help="Selection to be used by the TTree::Draw() method", metavar="treeSel")
    parser.add_option("--treeDrawOpt", type="string", dest="treeExpress", default="",
                    help="Draw expression to be passed to the TTree::Draw() method", metavar="treeExpress")
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
    strRootName = elogPath + "/gemTreeDrawWrapper_%s_vs_%s.root"%(options.branchName, strIndepVarNoBraces)
    r.gROOT.SetBatch(True)
    outF = r.TFile(strRootName,options.rootOpt)
    
    # Loop Over inVputs
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
       
        # Setup the path
        dirPath = getDirByAnaType(options.anaType.strip("Ana"), chamberAndScanDatePair[0], options.ztrim)
        if not filePathExists(dirPath, chamberAndScanDatePair[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, scandate)
            print 'Please cross-check, exiting!'
            outF.Close()
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, scandate, tree_names[options.anaType][0])
        treeName = tree_names[options.anaType][1]

        # Get the Plot
        thisPlot = getPlotFromTree(filename, treeName, options.treeExpress, options.treeSel)

        # Set the Stat Box Options
        if options.showStat:
            r.gStyle.SetOptStat(1111111)
        else:
            r.gStyle.SetOptStat(0000000)
        
        # Format this Plot
        thsCanvas = 
            # Draw this plot on a canvas
            strCanvName = elogPath + "/canv_%s_vs_%s_VFAT%i_%s.png"%(options.branchName,strIndepVarNoBraces, vfat,strStripOrChan)
            canvPlot.SetName("canv_%s_vs_%s_VFAT%i_%s"%(options.branchName,strIndepVarNoBraces, vfat, strStripOrChan))
            canvPlot.SetTitle("VFAT%i_%s: %s vs. %s"%(vfat,strStripOrChan,options.branchName,strIndepVarNoBraces))
            canvPlot.cd()
            grPlot.Draw(strDrawOpt)
            grPlot.GetXaxis().SetTitle(strIndepVar)
            grPlot.GetYaxis().SetDecimals(True)
            grPlot.GetYaxis().SetRangeUser(options.axisMin, options.axisMax)
            grPlot.GetYaxis().SetTitle(options.branchName)
            grPlot.GetYaxis().SetTitleOffset(1.2)

    # Make Summary Plot

    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
