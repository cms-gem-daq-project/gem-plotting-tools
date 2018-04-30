#!/bin/env python

def arbitraryPlotter(anaType, listDataPtTuples, rootFileName, treeName, branchName, vfat, vfatCH=None, strip=None, ztrim=4):
    """
    Provides a list of tuples for 1D data where each element is of the form: (indepVarVal, depVarVal, depVarValErr)

    anaType - type of analysis to perform, helps build the file path to the input file(s), from set ana_config.keys()
    listDataPtTuples - list of tuples where each element is of the form: (cName, scandate, indepVar), note indepVar is expected to be numeric
    rootFileName - name of the TFile that will be found in the data path corresponding to anaType
    treeName - name of the TTree inside rootFileName
    branchName - name of a branch inside treeName that the dependent variable will be extracted from
    vfat - vfat number that plots should be made for
    vfatCH - channel of the vfat that should be used, if None an average is performed w/stdev for error bar, mutually exclusive w/strip
    strip - strip of the detector that should be used, if None an average is performed w/stdev for error bar, mutually exclusive w/vfatCH
    """

    from gempython.gemplotting.anautilities import filePathExists, getDirByAnaType

    import numpy as np
    import os
    import root_numpy as rp

    # Make branches to load
    listNames = ["vfatN"]
    if vfatCH is not None and strip is None:
        listNames.append("vfatCH")
    elif strip is not None and vfatCH is None:
        listNames.append("ROBstr")
    listNames.append(branchName)

    # Load data
    listData = []
    for dataPt in listDataPtTuples:
        # Get human readable info
        cName = dataPt[0]
        scandate = dataPt[1]
        indepVarVal = dataPt[2]

        # Setup Paths
        dirPath = getDirByAnaType(anaType.strip("Ana"), cName, ztrim)
        if not filePathExists(dirPath, scandate):
            print 'Filepath %s/%s does not exist!'%(dirPath, scandate)
            print 'Please cross-check, exiting!'
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, scandate, rootFileName)

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

        # Check to make sure listNames are present in dataTree
        for testBranch in listNames:
            if testBranch not in knownBranches:
                print "Branch %s not in TTree %s of file %s"%(branchName, treeName, filename)
                print "Existing Branches are:"
                for realBranch in knownBranches:
                    print realBranch
                print "Please try again using one of the existing branches"
                #exit(os.EX_NOTFOUND) #Weird, not found but described in: https://docs.python.org/2/library/os.html#process-management
                exit(os.EX_DATAERR)

        # Get dependent variable value
        arrayVFATData = rp.tree2array(dataTree,listNames)
        dataThisVFAT = arrayVFATData[ arrayVFATData['vfatN'] == vfat] #VFAT Level

        # Close the TFile
        dataFile.Close()
        
        if vfatCH is not None and strip is None:
            dataThisVFAT = dataThisVFAT[ dataThisVFAT['vfatCH'] == vfatCH ] #VFAT Channel Level
        elif strip is not None and vfatCH is None:
            dataThisVFAT = dataThisVFAT[ dataThisVFAT['ROBstr'] == strip ] #Readout Board Strip Level
        
        depVarVal = np.asscalar(np.mean(dataThisVFAT[branchName]))   #If a vfatCH/ROBstr obs & chan/strip not give will be avg over all, else a number
        depVarValErr = np.asscalar(np.std(dataThisVFAT[branchName])) #If a vfatCH/ROBstr obs & chan/strip not given will be stdev over all, or zero

        #Record this dataPt
        listData.append( (indepVarVal, depVarVal, depVarValErr) )

    # Return Data
    return listData

def arbitraryPlotter2D(anaType, listDataPtTuples, rootFileName, treeName, branchName, vfat, ROBstr=True, ztrim=4):
    """
    Provides a list of tuples for 2D data where each element is of the (x,y,z) form: (indepVarVal, vfatCHOrROBstr, depVarVal)

    anaType - type of analysis to perform, helps build the file path to the input file(s), from set ana_config.keys()
    listDataPtTuples - list of tuples where each element is of the form: (cName, scandate, indepVar), note indepVar is expected to be numeric
    rootFileName - name of the TFile that will be found in the data path corresponding to anaType
    treeName - name of the TTree inside rootFileName
    branchName - name of a branch inside treeName that the dependent variable will be extracted from
    vfat - vfat number that plots should be made for
    """
  
    from gempython.gemplotting.anautilities import filePathExists, getDirByAnaType

    import numpy as np
    import os
    import root_numpy as rp

    # Make branches to load
    listNames = ["vfatN"]
    strChanName = "" #Name of channel TBranch, either 'ROBstr' or 'vfatCH'
    if ROBstr:
        listNames.append("ROBstr")
        strChanName = "ROBstr"
    else:
        listNames.append("vfatCH")
        strChanName = "vfatCH"
    listNames.append(branchName)

    # Load data
    listData = []
    for dataPt in listDataPtTuples:
        # Get human readable info
        cName = dataPt[0]
        scandate = dataPt[1]
        indepVarVal = dataPt[2]

        # Setup Paths
        dirPath = getDirByAnaType(anaType.strip("Ana"), cName, ztrim)
        if not filePathExists(dirPath, scandate):
            print 'Filepath %s/%s does not exist!'%(dirPath, scandate)
            print 'Please cross-check, exiting!'
            exit(os.EX_DATAERR)
        filename = "%s/%s/%s"%(dirPath, scandate, rootFileName)

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

        # Check to make sure listNames are present in dataTree
        for testBranch in listNames:
            if testBranch not in knownBranches:
                print "Branch %s not in TTree %s of file %s"%(branchName, treeName, filename)
                print "Existing Branches are:"
                for realBranch in knownBranches:
                    print realBranch
                print "Please try again using one of the existing branches"
                #exit(os.EX_NOTFOUND) #Weird, not found but described in: https://docs.python.org/2/library/os.html#process-management
                exit(os.EX_DATAERR)

        # Get dependent variable value - VFAT Level
        arrayVFATData = rp.tree2array(dataTree,listNames)
        dataThisVFAT = arrayVFATData[ arrayVFATData['vfatN'] == vfat] #VFAT Level

        # Close the TFile
        dataFile.Close()

        # Get the data for each strip and store it as a tuple in the list to be returned
        for chan in range(0,128):
            dataThisChan = dataThisVFAT[ dataThisVFAT[strChanName] == chan] #Channel Level
            depVarVal = np.asscalar(np.mean(dataThisChan[branchName]))
            listData.append( (indepVarVal, chan, depVarVal) )
            pass

    # Return Data
    return listData

if __name__ == '__main__':
    from gempython.gemplotting.anaInfo import tree_names
    from gempython.utils.wrappers import envCheck
    from plotoptions import parser

    import array
    import numpy as np
    import os
    import ROOT as r
    
    parser.add_option("-a","--all", action="store_true", dest="all_plots",
                    help="vfatList is automatically set to [0,1,...,22,23]", metavar="all_plots")
    parser.add_option("--alphaLabels", action="store_true", dest="alphaLabels",
                    help="Draw output plot using alphanumeric lables instead of pure floating point", metavar="alphaLabels")
    parser.add_option("--axisMax", type="float", dest="axisMax", default=255,
                    help="Maximum value for axis depicting branchName", metavar="axisMax")
    parser.add_option("--axisMin", type="float", dest="axisMin", default=0,
                    help="Minimum value for axis depicting branchName", metavar="axisMin")
    parser.add_option("--anaType", type="string", dest="anaType",
                    help="Analysis type to be executed, from list {'latency','scurve','scurveAna','threshold','trim','trimAna'}", metavar="anaType")
    parser.add_option("--branchName", type="string", dest="branchName",
                    help="Name of TBranch where dependent variable is store", metavar="branchName")
    parser.add_option("--make2D", action="store_true", dest="make2D",
                    help="A 2D plot of (indepVar, chan, branchName) is made instead of a 1D plot", metavar="make2D")
    parser.add_option("-p","--print", action="store_true", dest="printData",
                    help="Prints a comma separated table with the data to the terminal", metavar="printData")
    parser.add_option("--rootOpt", type="string", dest="rootOpt", default="RECREATE",
                    help="Option for the output TFile, e.g. {'RECREATE','UPDATE'}", metavar="rootOpt")
    parser.add_option("--showStat", action="store_true", dest="showStat",
                    help="Draws the statistics box for 2D plots", metavar="showStat")
    parser.add_option("--vfatList", type="string", dest="vfatList", default=None,
                    help="Comma separated list of VFATs to consider, e.g. '12,13'", metavar="vfatList")
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                    help="Specify the p value of the trim", metavar="ztrim")

    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()
  
    # Check Paths
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath  = os.getenv('ELOG_PATH')

    # Get VFAT List
    listVFATs = []
    if options.all_plots:
        listVFATs = (x for x in range(0,24))
    elif options.vfatList != None:
        listVFATs = map(int, options.vfatList.split(','))
    elif options.vfat != None:
        listVFATs.append(options.vfat)
    else:
        print "You must specify at least one VFAT to be considered"
        exit(os.EX_USAGE)
    
    # Check anaType is understood
    if options.anaType not in tree_names.keys():
        print "Invalid analysis specificed, please select only from the list:"
        print tree_names.keys()
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
    
    # Loop Over inputs
    strIndepVar = ""
    listDataPtTuples = []
    for i,line in enumerate(fileScanDates):
        if line[0] == "#":
            continue

        # Split the line
        line = line.strip('\n')
        analysisList = line.rsplit('\t') #chamber name, scandate, independent var

        if len(analysisList) != 3:
            print "Input format incorrect"
            print "I was expecting a tab-delimited file with each line having 3 entries"
            print "But I received:"
            print "\t%s"%(line)
            print "Exiting"
            exit(os.EX_USAGE)

        # On 1st iteration get independent variable name
        if i == 0:
            strIndepVar = analysisList[2]
            continue
        
        # Make input list for arbitraryPlotter()
        if options.alphaLabels:
            listDataPtTuples.append( (analysisList[0], analysisList[1], analysisList[2]) )
        else:
            try:
                listDataPtTuples.append( (analysisList[0], analysisList[1], float(analysisList[2]) ) )
            except Exception as e:
                print("Non-numeric input given, maybe you ment to call with option '--alphaLabels'?")
                print("Exiting")
                exit(os.EX_USAGE)
    
    # Do we make strip/channel level plot?
    vfatCH=None
    strip=None
    strDrawOpt = "APE1"
    strStripOrChan = "All"
    if options.strip is not None:
        # Set the strip or channel name
        if options.channels:
            vfatCH = options.strip
            strStripOrChan = "vfatCH%i"%options.strip
        else:
            strip = options.strip
            strStripOrChan = "ROBstr%i"%options.strip
    elif options.make2D:
        strDrawOpt = "COLZ"

        # Set the strip or channel name - no channel number here, over all of them
        if options.channels:
            strStripOrChan = "vfatCH"
        else:
            strStripOrChan = "ROBstr"
        
    # Get difference between independent variable values
    listIndepVarLowEdge = [] #used if either options.alphaLabels or options.make2D is true
    if options.alphaLabels:
        for i in range(0,len(listDataPtTuples)+1):
            listIndepVarLowEdge.append(i)
    elif options.make2D:
        listIndepVarVals = []
        arraydeltaIndepVar = np.zeros(len(listDataPtTuples)) #Difference between i and i+1 indepVar
        for i in range(0,len(listDataPtTuples)):
            listIndepVarVals.append(listDataPtTuples[i][2])
            if i == (len(listDataPtTuples) - 1):
                arraydeltaIndepVar[i] = 0.
            else:
                arraydeltaIndepVar[i] = np.fabs(listDataPtTuples[i][2] - listDataPtTuples[i+1][2])
        arraydeltaIndepVar[len(arraydeltaIndepVar)-1] = np.mean(arraydeltaIndepVar[:(len(arraydeltaIndepVar)-1)])

        # Set the values in listIndepVarLowEdge
        for i in range(0,len(listIndepVarVals)):
            if i == 0:
                # x_low_i = x_i - 0.5 * <delta_x>
                listIndepVarLowEdge.append(listIndepVarVals[i] - 0.5 * arraydeltaIndepVar[len(arraydeltaIndepVar)-1])
            else:
                # x_low_i = x_i - 0.5 * delta_x_(i-1)
                listIndepVarLowEdge.append(listIndepVarVals[i] - 0.5 * arraydeltaIndepVar[i-1])
        listIndepVarLowEdge.append(listIndepVarVals[len(listIndepVarVals)-1] + 0.5 * arraydeltaIndepVar[len(arraydeltaIndepVar)-1])

    # Loop over the vfats in listVFATs and make the requested plot for each
    strIndepVarNoBraces = strIndepVar.replace('{','').replace('}','').replace('_','')
    strRootName = "%s/gemPlotterOutput_%s_vs_%s.root"%(elogPath,options.branchName, strIndepVarNoBraces)
    r.gROOT.SetBatch(True)
    outF = r.TFile(strRootName,options.rootOpt)
    listPlots = []
    for vfat in listVFATs:
        # Make the output directory
        dirVFAT = r.TDirectory()
        if options.rootOpt.upper() == "UPDATE":
            dirVFAT = outF.GetDirectory("VFAT%i"%vfat, False, "GetDirectory")
        else:
            dirVFAT = outF.mkdir("VFAT%i"%vfat)
            pass

        # Make the output canvas, use a temp name and temp title for now
        strCanvName = ""
        canvPlot = r.TCanvas("canv_VFAT%i"%(vfat),"VFAT%i"%(vfat),600,600)

        # Make the plot, either 2D or 1D
        if options.make2D:
            listData = arbitraryPlotter2D(
                    options.anaType, 
                    listDataPtTuples, 
                    tree_names[options.anaType][0], 
                    tree_names[options.anaType][1], 
                    options.branchName, 
                    vfat,
                    not options.channels,
                    options.ztrim)

            # Print to the user
            if options.printData:
                print "===============Printing Data for VFAT%i==============="%(vfat)
                print "[BEGIN_DATA]"
                print "\tVAR_INDEP,VAR_DEP,VALUE"
                for dataPt in listData:
                    print "\t%f,%f,%f"%(dataPt[0],dataPt[1],dataPt[2])
                print "[END_DATA]"
                print ""
            

            # Make the plot
            binsIndepVarLowEdge = array.array('d',listIndepVarLowEdge)
            hPlot2D = r.TH2F("h_%s_vs_%s_Obs%s_VFAT%i"%(strStripOrChan, strIndepVarNoBraces, options.branchName, vfat),
                            "VFAT%i"%(vfat),
                            len(listIndepVarLowEdge)-1, binsIndepVarLowEdge,
                            128, -0.5, 127.5)
            hPlot2D.SetXTitle(strIndepVar)
            hPlot2D.SetYTitle(strStripOrChan)
            hPlot2D.SetZTitle(options.branchName)
           
            # Do we have alphanumeric bin labels?
            if options.alphaLabels:
                for binX,item in enumerate(listDataPtTuples):
                    hPlot2D.GetXaxis().SetBinLabel(binX+1,item[2])

            # Fill the plot
            for idx in range(len(listData)):
                hPlot2D.Fill(listData[idx][0],listData[idx][1],listData[idx][2])
            
            # Set the Stat Box Options
            if options.showStat:
                r.gStyle.SetOptStat(1111111)
            else:
                r.gStyle.SetOptStat(0000000)
                
            # Draw this plot on a canvas
            strCanvName = "%s/canv_%s_vs_%s_Obs%s_VFAT%i.png"%(elogPath, strStripOrChan, strIndepVarNoBraces, options.branchName, vfat)
            canvPlot.SetName("canv_%s_vs_%s_Obs%s_VFAT%i.png"%(strStripOrChan, strIndepVarNoBraces, options.branchName, vfat))
            canvPlot.SetTitle("VFAT%i: %s vs. %s - Obs %s"%(vfat,strStripOrChan,strIndepVarNoBraces, options.branchName))
            canvPlot.SetRightMargin(0.15)
            canvPlot.cd()
            hPlot2D.GetZaxis().SetRangeUser(options.axisMin, options.axisMax)
            hPlot2D.Draw(strDrawOpt)
            hPlot2D.GetYaxis().SetDecimals(True)
            hPlot2D.GetYaxis().SetTitleOffset(1.2)
            
            # Store the plot
            dirVFAT.cd()
            hPlot2D.Write()
            listPlots.append(hPlot2D)
        else:
            listData = arbitraryPlotter(
                    options.anaType, 
                    listDataPtTuples, 
                    tree_names[options.anaType][0], 
                    tree_names[options.anaType][1], 
                    options.branchName, 
                    vfat, 
                    vfatCH, 
                    strip,
                    options.ztrim)

            # Print to the user
            # Using format compatible with: https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data
            if options.printData:
                print "===============Printing Data for VFAT%i==============="%(vfat)
                print "[BEGIN_DATA]"
                print "\tVAR_INDEP,VAR_DEP,VAR_DEP_ERR"
                for dataPt in listData:
                    print "\t%f,%f,%f"%(dataPt[0],dataPt[1],dataPt[2])
                print "[END_DATA]"
                print ""

            # Make the plot
            thisPlot = r.TGraphErrors(len(listData))
            if options.alphaLabels:
                strDrawOpt = "PE1v"
                
                binsIndepVarLowEdge = array.array('d',listIndepVarLowEdge)
                thisPlot = r.TH1F("h_%s_vs_%s_VFAT%i_%s"%(options.branchName, strIndepVarNoBraces, vfat, strStripOrChan),
                                  "VFAT%i_%s"%(vfat,strStripOrChan),
                                  len(listIndepVarLowEdge)-1, binsIndepVarLowEdge)
           
                for binX,item in enumerate(listDataPtTuples):
                    thisPlot.GetXaxis().SetBinLabel(binX+1,item[2])
                for idx in range(len(listData)):
                    thisPlot.Fill(listData[idx][0], listData[idx][1])
                    
                    if thisPlot.GetXaxis().GetBinLabel(idx+1) == listDataPtTuples[idx][2]:
                        thisPlot.SetBinError(idx+1, listData[idx][2])
            else:
                thisPlot.SetTitle("VFAT%i_%s"%(vfat,strStripOrChan))
                thisPlot.SetName("g_%s_vs_%s_VFAT%i_%s"%(options.branchName, strIndepVarNoBraces, vfat, strStripOrChan))
                for idx in range(len(listData)):
                    thisPlot.SetPoint(idx, listData[idx][0], listData[idx][1])
                    thisPlot.SetPointError(idx, 0., listData[idx][2])

            # Draw this plot on a canvas
            thisPlot.SetMarkerStyle(20)
            thisPlot.SetLineWidth(2)
            strCanvName = "%s/canv_%s_vs_%s_VFAT%i_%s.png"%(elogPath, options.branchName,strIndepVarNoBraces, vfat,strStripOrChan)
            canvPlot.SetName("canv_%s_vs_%s_VFAT%i_%s"%(options.branchName,strIndepVarNoBraces, vfat, strStripOrChan))
            canvPlot.SetTitle("VFAT%i_%s: %s vs. %s"%(vfat,strStripOrChan,options.branchName,strIndepVarNoBraces))
            canvPlot.cd()
            thisPlot.Draw(strDrawOpt)
            thisPlot.GetXaxis().SetTitle(strIndepVar)
            thisPlot.GetXaxis().SetLabelSize(0.04)
            thisPlot.GetYaxis().SetDecimals(True)
            thisPlot.GetYaxis().SetRangeUser(options.axisMin, options.axisMax)
            thisPlot.GetYaxis().SetTitle(options.branchName)
            thisPlot.GetYaxis().SetTitleOffset(1.2)
        
            # Store the plot
            dirVFAT.cd()
            thisPlot.Write()
            listPlots.append(thisPlot)
            pass
        
        if not options.all_plots:
            print ""
            print "To view your plot, execute:"
            print ("eog " + strCanvName)
            print ""

        # Store the Canvas
        canvPlot.Update()
        canvPlot.SaveAs(strCanvName)
        dirVFAT.cd()
        canvPlot.Write()
        pass

    # Make Summary Plot
    if options.all_plots:
        from gempython.gemplotting.anautilities import make3x8Canvas
        strSummaryName = "summary_%s_vs_%s_%s"%(options.branchName, strIndepVarNoBraces,strStripOrChan)
        canv_summary = make3x8Canvas( strSummaryName, listPlots, strDrawOpt)
        
        strCanvName = "%s/%s.png"%(elogPath,strSummaryName)
        canv_summary.SaveAs(strCanvName)
        
        outF.cd()
        canv_summary.Write()

        print ""
        print "To view your plot, execute:"
        print ("eog " + strCanvName)
        print ""

    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
