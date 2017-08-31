#!/bin/env python

# Returns binomial error on eff
def calcEffErr(eff, nTriggers):
    import math
    return math.sqrt( (eff * ( 1. - eff) ) / nTriggers )

# Returns a tuple of (eff, sigma_eff)
def calcEff(cName, scandate, vfatList, latBin):
    import os

    # Setup paths
    dataPath  = os.getenv('DATA_PATH')
    dirPath = "%s/%s/latency/trk/%s/"%(dataPath,cName,scandate)
    filename = dirPath + "LatencyScanData.root"

    # Load data
    import root_numpy as rp
    import numpy as np
    list_bNames = ["vfatN","lat","Nhits","Nev"]
    try:
        array_VFATData = rp.root2array(filename,"latTree",list_bNames)
        pass
    except Exception as e:
        print '%s does not seem to exist'%filename
        print e
        pass

    # Determine hits and triggers
    nTriggers = np.asscalar(np.unique(array_VFATData['Nev']))
    nHits = 0.0
    for vfat in vfatList:
        vfatData = array_VFATData[ array_VFATData['vfatN'] == vfat]
        latData = vfatData[vfatData['lat'] == latBin]
        nHits += np.asscalar(latData['Nhits'])

    # Calc Eff & Error
    return (nHits / nTriggers, calcEffErr(nHits / nTriggers, nTriggers) )

# Here --infilename should be a tab delimited file
#   the first row of this file should be column headings
#   the subsequent rows of this file should be data lines
#   Example:
#       ChamberName scandate    EffGain
#       GEMINIm27L1 2017.08.29.18.11    5000
#       GEMINIm27L1 2017.08.29.18.19    7500
#       GEMINIm27L1 2017.08.29.18.33    10000
#       GEMINIm27L1 2017.08.29.18.06    15000
#       GEMINIm27L1 2017.08.30.08.22    20000
#
#   Then this will make a plot of Eff vs. EffGain from the data supplied
if __name__ == '__main__':
    from gempython.utils.wrappers import envCheck
    from macros.plotoptions import parser
    from mapping.chamberInfo import chamber_config, GEBtype
    
    import os
    
    parser.add_option("--latSig", type="int", dest="latSig", default=None,
                      help="Latency bin where signal is found", metavar="latSig")
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

    # Check that the user supplied a latency value
    if options.latSig == None:
        print "You must specify the latency bin of the signal peak"
        exit(-1)
    
    # Loop Over inputs
    fileScanDates = open(options.filename, 'r') #tab '\t' delimited file, first line column headings, subsequent lines data: cName\tscandate\tindepvar
    list_EffData = []
    strIndepVar = ""
    strChamberName = ""
    for i,line in enumerate(fileScanDates):
        # Split the line
        line = line.strip('\n')
        analysisList = line.rsplit('\t') #chamber name, scandate, independent var

        # On 1st iteration get independent variable name
        if i == 0:
            #strChamberName = analysisList[0]
            strIndepVar = analysisList[2]
            continue

        if len(strChamberName) == 0 and i > 0:
            strChamberName = analysisList[0]
        
        tuple_eff = calcEff(analysisList[0], analysisList[1], list_VFATs, options.latSig)
        list_EffData.append((float(analysisList[2]), tuple_eff[0], tuple_eff[1]))

    # Print to the user
    # Using format compatible with: https://github.com/cms-gem-detqc-project/CMS_GEM_Analysis_Framework#4eiviii-header-parameters---data
    if options.printData:
        print ""
        print "[BEGIN_DATA]"
        print "\tVAR_INDEP,VAR_DEP,VAR_DEP_ERR"
        for dataPt in list_EffData:
            print "\t%f,%f,%f"%(dataPt[0],dataPt[1],dataPt[2])
        print "[END_DATA]"
        print ""

    # Plot the efficiency plot
    import ROOT as r
    r.gROOT.SetBatch(True)
    grEffPlot = r.TGraphErrors(len(list_EffData))
    grEffPlot.SetTitle("Eff from VFATs: [%s]"%(options.vfatList))
    grEffPlot.SetMarkerStyle(20)
    grEffPlot.SetLineWidth(2)
    for idx in range(len(list_EffData)):
        grEffPlot.SetPoint(idx, list_EffData[idx][0], list_EffData[idx][1])
        grEffPlot.SetPointError(idx, 0., list_EffData[idx][2])

    # Draw this plot on a canvas
    strIndepVarNoBrances = strIndepVar.replace('{','').replace('}','').replace('_','')
    canvEff = r.TCanvas("%s_Eff_vs_%s"%(strChamberName,strIndepVarNoBrances),"%s: Eff vs. %s"%(strChamberName,strIndepVarNoBrances),600,600)
    canvEff.cd()
    grEffPlot.Draw("APE1")
    grEffPlot.GetXaxis().SetTitle(strIndepVar)
    grEffPlot.GetYaxis().SetDecimals(True)
    grEffPlot.GetYaxis().SetRangeUser(0.0,1.0)
    grEffPlot.GetYaxis().SetTitle("Efficiency")
    grEffPlot.GetYaxis().SetTitleOffset(1.2)
    canvEff.Update()
    strCanvName = elogPath + "/%s_Eff_vs_%s.png"%(strChamberName,strIndepVarNoBrances)
    canvEff.SaveAs(strCanvName)
    
    print ""
    print "To view your plot, execute:"
    print ("eog " + strCanvName)
    print ""

    # Make an output ROOT file
    strRootName = elogPath + "/%s_Eff_vs_%s.root"%(strChamberName,strIndepVarNoBrances)
    outF = r.TFile(strRootName,"recreate")
    grEffPlot.Write()
    canvEff.Write()
    
    print ""
    print "Your plot is stored in a TFile, to open it execute:"
    print ("root " + strRootName)
    print ""
