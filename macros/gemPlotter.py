#!/bin/env python


# listDataPtTuples[i] = (cName, scandate, indepVar)
def arbitraryPlotter(anaType, listDataPtTuples, rootFileName, treeName, branchName, vfat, vfatCh=None, strip=None):
    """

    dataPath/<scandates>/<dirname>/<root file>

    """
  
    from anautilities import getDirByAnaType

    import numpy as np
    import root_numpy as rp

    # Make branches to load
    list_bNames = ["vfatN"]
    if vfatCh is not None and strip is None:
        list_bNames.append("vfatCH")
    elif strip is not None and vfatCh is None:
        list_bNames.append("ROBstr")
    list_bNames.append(branchName)

    # Load data
    list_Data = []
    for dataPt in listDataPtTuples:
        # Get human readable info
        cName = dataPt[0]
        scandate = dataPt[1]
        indepVarVal = dataPt[2]

        # Setup Paths
        dirPath = getDirByAnaType(anaType, cName, ztrim=4)
        filename = "%s/%s/%s"%(dirPath, scandate, rootFileName)

        try:
            array_VFATData = rp.root2array(filename,treeName,list_bNames)
            pass
        except Exception as e:
            print '%s does not seem to exist'%filename
            print e
            pass

        # Get dependent variable value
        dataThisVFAT = array_VFATData[ array_VFATData['vfatN'] == vfat] #VFAT Level
        if vfatCh is not None and strip is None:
            dataThisVFAT = dataThisVFAT[ dataThisVFAT['vfatCH'] == vfatCh ] #VFAT Channel Level
        elif strip is not None and vfatCh is None:
            dataThisVFAT = dataThisVFAT[ dataThisVFAT['ROBstr'] == vfatCh ] #Readout Board Strip Level
        
        depVarVal = np.mean(dataThisVFAT[branchName])   #If a vfatCH/ROBstr obs & chan/strip not give will be avg over all, else a number
        depVarValErr = np.std(dataThisVFAT[branchName]) #If a vfatCH/ROBstr obs & chan/strip not given will be stdev over all, or zero

        #Record this dataPt
        list_Data.append( (indepVarVal, depVarVal, depVarValErr) )

    # Return Data
    return list_Data

if __name__ == '__main__':
    from anaInfo import tree_names
    from gempython.utils.wrappers import envCheck
    from macros.plotoptions import parser
    from mapping.chamberInfo import chamber_config
    
    import os
    
    parser.add_option("--anaType", type="string", dest="anaType",
                     help="Analysis type to be executed, from list {'latency','scurve','scurveAna','threshold','trim','trimAna'}", metavar="anaType")
    parser.add_option("--branchName", type="string", dest="branchName",
                     help="Name of TBranch where dependent variable is store", metavar="branchName")
    parser.add_option("-p","--print", action="store_true", dest="printData",
                      help="Prints a comma separated table with the data to the terminal", metavar="printData")
    parser.add_option("--scandate", type="string", dest="scandate", default="current",
                      help="Specify specific date to analyze", metavar="scandate")
    parser.add_option("--vfatList", type="string", dest="vfatList", default=None,
                      help="Comma separated list of VFATs to consider, e.g. '12,13'", metavar="vfatList")

    parser.set_defaults(filename="listOfScanDates.txt")
    (options, args) = parser.parse_args()
  
    # Check Paths
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath  = os.getenv('ELOG_PATH')

    # Get VFAT List
    list_VFATs = []
    if options.vfatList != None:
        list_VFATs = map(int, options.vfatList.split(','))
    elif options.vfat != None:
        list_VFATs.append(options.vfat)
    else:
        print "You must specify at least one VFAT to be considered"
        exit(-1)

    # Check anaType is understood
    if options.anaType not in tree_names.keys():
        print "Invalid analysis specificed, please select only from the list:"
        print tree_names.keys()
        exit(-2)
        pass
    
    # Loop Over inputs
    fileScanDates = open(options.filename, 'r') #tab '\t' delimited file, first line column headings, subsequent lines data: cName\tscandate\tindepvar
    strIndepVar = ""
    #strChamberName = ""
    #listDataPtTuples[i] = (cName, scandate, indepVar)
    listDataPtTuples = []
    for i,line in enumerate(fileScanDates):
        # Split the line
        line = line.strip('\n')
        analysisList = line.rsplit('\t') #chamber name, scandate, independent var

        # On 1st iteration get independent variable name
        if i == 0:
            strIndepVar = analysisList[2]
            continue

        # On 1st iteration get indep
        #if len(strChamberName) == 0 and i > 0:
        #    strChamberName = analysisList[0]
       
        # Make input list for arbitraryPlotter()
        listDataPtTuples.append( (analysisList[0], analysisList[1], analysisList[2] ) )

    # Do we make strip/channel level plot?
    vfatCh=None
    strip=None
    if options.strip is not None:
        if options.channels:
            vfatCh = options.strip
        else
            strip = options.strip

    # Get the Requested Data & Store it in an output ROOT File
    strIndepVarNoBraces = strIndepVar.replace('{','').replace('}','').replace('_','')
    strRootName = elogPath + "/gemPlotterOutput_%s_vs_%s.root"%(options.branchName, strIndepVarNoBraces)
    outF = r.TFile(strRootName,"recreate")
    for vfat in options.vfatList:
        list_Data = arbitraryPlotter(
                options.anaType, 
                listDataPtTuples, 
                tree_names[options.anaType][0], 
                tree_names[options.anaType][1], 
                options.branchName, 
                options.vfat, 
                vfatCh, 
                strip)

        # Print to the user
        # Using format compatible with: https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data
        if options.printData:
            print "===============Printing Data for VFAT%i==============="%(vfat)
            print "[BEGIN_DATA]"
            print "\tVAR_INDEP,VAR_DEP,VAR_DEP_ERR"
            for dataPt in list_Data:
                print "\t%f,%f,%f"%(dataPt[0],dataPt[1],dataPt[2])
            print "[END_DATA]"
            print ""

        # Make the plot
        import ROOT as r
        r.gROOT.SetBatch(True)
        grPlot = r.TGraphErrors(len(list_Data))
        grPlot.SetName("g_%s_vs_%s_VFAT%i"%(options.branchName, strIndepVarNoBraces, vfat)
        grPlot.SetMarkerStyle(20)
        grPlot.SetLineWidth(2)
        for idx in range(len(list_Data)):
            grPlot.SetPoint(idx, list_Data[idx][0], list_Data[idx][1])
            grPlot.SetPointError(idx, 0., list_Data[idx][2])

        # Draw this plot on a canvas
        canvPlot = r.TCanvas("canv_%s_vs_%s_VFAT%i"%(options.branchName,strIndepVarNoBraces, vfat),"VFAT%i: %s vs. %s"%(vfat,options.branchName,strIndepVarNoBraces),600,600)
        canvPlot.cd()
        grPlot.Draw("APE1")
        grPlot.GetXaxis().SetTitle(strIndepVar)
        grPlot.GetYaxis().SetDecimals(True)
        grPlot.GetYaxis().SetRangeUser(0.0,1.0)
        grPlot.GetYaxis().SetTitle(options.branchName)
        grPlot.GetYaxis().SetTitleOffset(1.2)
        canvPlot.Update()
        strCanvName = elogPath + "/canv_%s_vs_%s_VFAT%i"%(options.branchName,strIndepVarNoBraces, vfat)
        canvPlot.SaveAs(strCanvName)
        
        print ""
        print "To view your plot, execute:"
        print ("eog " + strCanvName)
        print ""

        outF.cd()
        grPlot.Write()
        canvPlot.Write()
        pass

    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
