r"""
``latAlgos`` --- Utilities for analyzing lat scan data
============================================================

.. code-block:: python

    import gempython.gemplotting.utils.latAlgos

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Utilities for analyzing latency scan data

Documentation
-------------
"""

def anaUltraLatencyStar(inputs):
    """
    Wrapper to be used with multiprocessing.Pool methods
    See: https://stackoverflow.com/questions/5442910/python-multiprocessing-pool-map-for-multiple-arguments
    
    When moving to python 3.X we should use the Pool::starmap function and not this wrapper:
    see: https://stackoverflow.com/a/5442981
    """
    return anaUltraLatency(*inputs)

def anaUltraLatency(infilename, debug=False, latSigMaskRange=None, latSigRange=None, outputDir=None, outfilename="latencyAna.root", performFit=False):
    """
    Analyzes data taken by ultraLatency.py

    infilename      - Name of input TFile containing the latTree TTree
    debug           - If True prints additional debugging statements
    latSigMaskRange - Comma separated pair of values defining the region 
                      to be masked when trying to fit the noise, e.g. 
                      lat #notepsilon [40,44] is noise (lat < 40 || lat > 44)")
    latSigRange     - Comma separated pair of values defining expected 
                      signal range, e.g. lat #epsilon [41,43] is signal")
    outfilename  - Name of output TFile containing analysis results
    performFit      - Fit the latency distributions    
    """

    # Determine output filepath
    if outputDir is None:
        from gempython.gemplotting.utils.anautilities import getElogPath
        outputDir = getElogPath()
        pass

    # Redirect sys.stdout and sys.stderr if necessary 
    from gempython.gemplotting.utils.multiprocUtils import redirectStdOutAndErr
    redirectStdOutAndErr("anaUltraLatency",outputDir)

    # Create the output File and TTree
    import ROOT as r
    outF = r.TFile(outputDir+"/"+outfilename,"RECREATE")
    if not outF.IsOpen():
        outF.Close()
        raise IOError("Unable to open output file {1} check to make sure you have write permissions under {0}".format(outputDir,outfilename))
    if outF.IsZombie():
        outF.Close()
        raise IOError("Output file {1} is a Zombie, check to make sure you have write permissions under {0}".format(outputDir,outfilename))
    myT = r.TTree('latFitTree','Tree Holding FitData')

    # Attempt to open input TFile
    inFile = r.TFile(infilename,"read")
    if not inFile.IsOpen():
        outF.Close()
        inFile.Close()
        raise IOError("Unable to open input file {0} check to make sure you have read permissions".format(infilename))
    if inFile.IsZombie():
        outF.Close()
        inFile.Close()
        raise IOError("Input file {0} is a Zombie, check to make sure you have write permissions and file has expected size".format(infilename))

    from gempython.tools.hw_constants import vfatsPerGemVariant
    # Get ChipID's
    import numpy as np
    import root_numpy as rp

    ##### FIXME
    from gempython.gemplotting.mapping.chamberInfo import gemTypeMapping
    if 'gemType' not in inFile.latTree.GetListOfBranches():
        gemType = "ge11"
    else:
        gemType = gemTypeMapping[rp.tree2array(tree=inFile.latTree, branches =[ 'gemType' ] )[0][0]]
    print gemType
    ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans    


    
    listOfBranches = inFile.latTree.GetListOfBranches()
    if 'vfatID' in listOfBranches:
        array_chipID = np.unique(rp.tree2array(inFile.latTree, branches = [ 'vfatID','vfatN' ] ))
        dict_chipID = {}
        for entry in array_chipID:
            dict_chipID[entry['vfatN']]=entry['vfatID']
    else:
        dict_chipID = { vfat:0 for vfat in range(nVFATS) }

    if debug:
        print("VFAT Position to ChipID Mapping")
        for vfat,vfatID in dict_chipID.iteritems():
            print(vfat,vfatID)
    
    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    #Initializing Histograms
    print('Initializing Histograms')
    from gempython.utils.gemlogger import printYellow
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_hVFATHitsVsLat = ndict()
    for vfat in range(0,nVFATS):
        try:
            chipID = dict_chipID[vfat]
        except KeyError as err:
            chipID = 0
            if debug:
                printYellow("No CHIP_ID for VFAT{0}, If you don't expect data from this VFAT there's no problem".format(vfat))
        
        dict_hVFATHitsVsLat[vfat] = r.TH1F("vfat{0}HitsVsLat".format(vfat),"VFAT {0}: chipID {1}".format(vfat,chipID),1024,-0.5,1023.5)
        pass

    #Filling Histograms
    print('Filling Histograms')
    latMin = 1000
    latMax = -1
    nTrig = -1
    for event in inFile.latTree:
        dict_hVFATHitsVsLat[int(event.vfatN)].Fill(event.latency,event.Nhits)
        if event.latency < latMin and event.Nhits > 0:
            latMin = event.latency
            pass
        elif event.latency > latMax:
            latMax = event.latency
            pass

        if nTrig < 0:
            nTrig = event.Nev
            pass
        pass

    from math import sqrt
    for vfat in range(0,nVFATS):
        for binX in range(1, dict_hVFATHitsVsLat[vfat].GetNbinsX()+1):
            dict_hVFATHitsVsLat[vfat].SetBinError(binX, sqrt(dict_hVFATHitsVsLat[vfat].GetBinContent(binX)))

    hHitsVsLat_AllVFATs = dict_hVFATHitsVsLat[0].Clone("hHitsVsLat_AllVFATs")
    hHitsVsLat_AllVFATs.SetTitle("Sum over all VFATs")
    for vfat in range(1,nVFATS):
        hHitsVsLat_AllVFATs.Add(dict_hVFATHitsVsLat[vfat])

    # Set Latency Fitting Bounds - Signal
    latFitMin_Sig = latMin
    latFitMax_Sig = latMax
    if latSigRange is not None:
        listLatValues = map(lambda val: float(val), latSigRange.split(","))
        if len(listLatValues) != 2:
            raise IndexError("You must specify exactly two values for determining latency signal range; values given: {0} do not meet this criterion".format(listLatValues))
        else:
            latFitMin_Sig = min(listLatValues)
            latFitMax_Sig = max(listLatValues)

    # Set Latency Fitting Bounds - Noise
    latFitMin_Noise = latFitMin_Sig - 1
    latFitMax_Noise = latFitMax_Sig + 1
    if latSigMaskRange is not None:
        listLatValues = map(lambda val: float(val), latSigMaskRange.split(","))
        if len(listLatValues) != 2:
            raise IndexError("You must specify exactly two values for determining latency signal range; values given: {0} do not meet this criterion".format(listLatValues))
        else:
            latFitMin_Noise = min(listLatValues)
            latFitMax_Noise = max(listLatValues)

    # Make output TFile and TTree
    from array import array
    dirVFATPlots = outF.mkdir("VFAT_Plots")
    if 'detName' in listOfBranches:    
        detName = r.vector('string')()
        detName.push_back(rp.tree2array(inFile.latTree, branches = [ 'detName' ] )[0][0][0])
        myT.Branch( 'detName', detName)
    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vfatID = array( 'L', [0] )
    myT.Branch( 'vfatID', vfatID, 'vfatID/i' ) #Hex Chip ID of VFAT
    hitCountMaxLat = array( 'f', [ 0 ] )
    myT.Branch( 'hitCountMaxLat', hitCountMaxLat, 'hitCountMaxLat/F' )
    hitCountMaxLatErr = array( 'f', [ 0 ] )
    myT.Branch( 'hitCountMaxLatErr', hitCountMaxLatErr, 'hitCountMaxLatErr/F' )
    maxLatBin = array( 'f', [ 0 ] )
    myT.Branch( 'maxLatBin', maxLatBin, 'maxLatBin/F' )
    hitCountBkg = array( 'f', [ 0 ] )
    hitCountBkgErr = array( 'f', [ 0 ] )
    hitCountSig = array( 'f', [ 0 ] )
    hitCountSigErr = array( 'f', [ 0 ] )
    SigOverBkg = array( 'f', [ 0 ] )
    SigOverBkgErr = array( 'f', [ 0 ] )
    if performFit:
        myT.Branch( 'hitCountBkg', hitCountBkg, 'hitCountBkg/F')
        myT.Branch( 'hitCountBkgErr', hitCountBkgErr, 'hitCountBkgErr/F')
        myT.Branch( 'hitCountSig', hitCountSig, 'hitCountSig/F')
        myT.Branch( 'hitCountSigErr', hitCountSigErr, 'hitCountSigErr/F')
        myT.Branch( 'SigOverBkg', SigOverBkg, 'SigOverBkg/F')
        myT.Branch( 'SigOverBkgErr', SigOverBkgErr, 'SigOverBkgErr/F')

    # Make output plots
    from math import sqrt
    dict_grNHitsVFAT = ndict()
    dict_fitNHitsVFAT_Sig = ndict()
    dict_fitNHitsVFAT_Noise = ndict()
    grNMaxLatBinByVFAT = r.TGraphErrors(len(dict_hVFATHitsVsLat))
    grMaxLatBinByVFAT = r.TGraphErrors(len(dict_hVFATHitsVsLat))
    grVFATSigOverBkg = r.TGraphErrors(len(dict_hVFATHitsVsLat))
    grVFATNSignalNoBkg = r.TGraphErrors(len(dict_hVFATHitsVsLat))
    r.gStyle.SetOptStat(0)
    if debug and performFit:
        print("VFAT\tSignalHits\tSignal/Noise")

    for vfat in dict_hVFATHitsVsLat:
        #if we don't have any data for this VFAT, we just need to initialize the TGraphAsymmErrors since it is drawn later
        if vfat not in dict_chipID:
            dict_grNHitsVFAT[vfat] = r.TGraphAsymmErrors()
            continue
        
        # Store VFAT info
        vfatN[0] = vfat
        vfatID[0] = dict_chipID[vfat]

        # Store Max Info
        hitCountMaxLat[0] = dict_hVFATHitsVsLat[vfat].GetBinContent(dict_hVFATHitsVsLat[vfat].GetMaximumBin())
        hitCountMaxLatErr[0] = sqrt(hitCountMaxLat[0])
        grNMaxLatBinByVFAT.SetPoint(vfat, vfat, hitCountMaxLat[0])
        grNMaxLatBinByVFAT.SetPointError(vfat, 0, hitCountMaxLatErr[0])

        maxLatBin[0] = dict_hVFATHitsVsLat[vfat].GetBinCenter(dict_hVFATHitsVsLat[vfat].GetMaximumBin())
        grMaxLatBinByVFAT.SetPoint(vfat, vfat, maxLatBin[0])
        grMaxLatBinByVFAT.SetPointError(vfat, 0, 0.5) #could be improved upon

        # Initialize
        dict_fitNHitsVFAT_Sig[vfat] = r.TF1("func_N_vs_Lat_VFAT{0}_Sig".format(vfat),"[0]",latFitMin_Sig,latFitMax_Sig)
        dict_fitNHitsVFAT_Noise[vfat] = r.TF1("func_N_vs_Lat_VFAT{0}_Noise".format(vfat),"[0]",latMin,latMax)
        dict_grNHitsVFAT[vfat] = r.TGraphAsymmErrors(dict_hVFATHitsVsLat[vfat])
        dict_grNHitsVFAT[vfat].SetName("g_N_vs_Lat_VFAT{0}".format(vfat))

        # Fitting
        if performFit:
            # Fit Signal
            dict_fitNHitsVFAT_Sig[vfat].SetParameter(0, hitCountMaxLat[0])
            dict_fitNHitsVFAT_Sig[vfat].SetLineColor(r.kGreen+1)
            dict_grNHitsVFAT[vfat].Fit(dict_fitNHitsVFAT_Sig[vfat],"QR")

            # Remove Signal Region
            latVal = r.Double()
            hitVal = r.Double()
            gTempDist = dict_grNHitsVFAT[vfat].Clone("g_N_vs_Lat_VFAT{0}_NoSig".format(vfat))
            for idx in range(dict_grNHitsVFAT[vfat].GetN()-1,0,-1):
                gTempDist.GetPoint(idx,latVal,hitVal)
                if latFitMin_Noise < latVal and latVal < latFitMax_Noise:
                    gTempDist.RemovePoint(idx)

            # Fit Noise
            dict_fitNHitsVFAT_Noise[vfat].SetParameter(0, 0.)
            dict_fitNHitsVFAT_Noise[vfat].SetLineColor(r.kRed+1)
            gTempDist.Fit(dict_fitNHitsVFAT_Noise[vfat],"QR")

            # Calc Signal & Signal/Noise
            hitCountBkg[0] = dict_fitNHitsVFAT_Noise[vfat].GetParameter(0)
            hitCountBkgErr[0] = dict_fitNHitsVFAT_Noise[vfat].GetParError(0)
            hitCountSig[0] = dict_fitNHitsVFAT_Sig[vfat].GetParameter(0) - hitCountBkg[0]
            hitCountSigErr[0] = sqrt( (dict_fitNHitsVFAT_Sig[vfat].GetParError(0))**2 + hitCountBkgErr[0]**2)

            SigOverBkg[0] = hitCountSig[0] / hitCountBkg[0]
            SigOverBkgErr[0] = sqrt( (hitCountSigErr[0] / hitCountBkg[0])**2 + (hitCountBkgErr[0]**2 * (hitCountSig[0] / hitCountBkg[0]**2)**2) )

            # Add to Plot
            grVFATSigOverBkg.SetPoint(vfat, vfat, SigOverBkg[0] )
            grVFATSigOverBkg.SetPointError(vfat, 0, SigOverBkgErr[0] )

            grVFATNSignalNoBkg.SetPoint(vfat, vfat, hitCountSig[0] )
            grVFATNSignalNoBkg.SetPointError(vfat, 0, hitCountSigErr[0] )

            # Print if requested
            if debug:
                print("{0}\t{1}\t{2}".format(vfat, hitCountSig[0], SigOverBkg[0]))
            pass

        # Format
        r.gStyle.SetOptStat(0)
        dict_grNHitsVFAT[vfat].SetMarkerStyle(21)
        dict_grNHitsVFAT[vfat].SetMarkerSize(0.7)
        dict_grNHitsVFAT[vfat].SetLineWidth(2)
        dict_grNHitsVFAT[vfat].GetXaxis().SetRangeUser(latMin, latMax)
        dict_grNHitsVFAT[vfat].GetXaxis().SetTitle("Lat")
        dict_grNHitsVFAT[vfat].GetYaxis().SetRangeUser(0, nTrig)
        dict_grNHitsVFAT[vfat].GetYaxis().SetTitle("N")

        # Write
        dirVFAT = dirVFATPlots.mkdir("VFAT{0}".format(vfat))
        dirVFAT.cd()
        dict_grNHitsVFAT[vfat].Write()
        dict_hVFATHitsVsLat[vfat].Write()
        if performFit:
            dict_fitNHitsVFAT_Sig[vfat].Write()
            dict_fitNHitsVFAT_Noise[vfat].Write()
        myT.Fill()
        pass

    # Store - Summary
    from gempython.gemplotting.utils.anautilities import getSummaryCanvas, addPlotToCanvas
    if performFit:
        canv_Summary = getSummaryCanvas(dict_grNHitsVFAT, name='canv_Summary', drawOpt='APE1', gemType=gemType)
        canv_Summary = addPlotToCanvas(canv_Summary, dict_fitNHitsVFAT_Noise, gemType)
        canv_Summary.SaveAs(outputDir+'/Summary.png')
    else:
        canv_Summary = getSummaryCanvas(dict_grNHitsVFAT, name='canv_Summary', drawOpt='APE1', gemType=gemType)
        canv_Summary.SaveAs(outputDir+'/Summary.png')

    # Store - Sig Over Bkg
    if performFit:
        canv_SigOverBkg = r.TCanvas("canv_SigOverBkg","canv_SigOverBkg",600,600)
        canv_SigOverBkg.cd()
        canv_SigOverBkg.cd().SetLogy()
        canv_SigOverBkg.cd().SetGridy()
        grVFATSigOverBkg.SetTitle("")
        grVFATSigOverBkg.SetMarkerStyle(21)
        grVFATSigOverBkg.SetMarkerSize(0.7)
        grVFATSigOverBkg.SetLineWidth(2)
        grVFATSigOverBkg.GetXaxis().SetTitle("VFAT Pos")
        grVFATSigOverBkg.GetYaxis().SetTitle("Sig / Bkg)")
        grVFATSigOverBkg.GetYaxis().SetTitleOffset(1.25)
        grVFATSigOverBkg.GetYaxis().SetRangeUser(1e-1,1e2)
        grVFATSigOverBkg.GetXaxis().SetRangeUser(-0.5,nVFATS +0.5)
        grVFATSigOverBkg.Draw("APE1")
        canv_SigOverBkg.SaveAs(outputDir+'/SignalOverBkg.png')

    # Store - Signal
    if performFit:
        canv_Signal = r.TCanvas("canv_Signal","canv_Signal",600,600)
        canv_Signal.cd()
        grVFATNSignalNoBkg.SetTitle("")
        grVFATNSignalNoBkg.SetMarkerStyle(21)
        grVFATNSignalNoBkg.SetMarkerSize(0.7)
        grVFATNSignalNoBkg.SetLineWidth(2)
        grVFATNSignalNoBkg.GetXaxis().SetTitle("VFAT Pos")
        grVFATNSignalNoBkg.GetYaxis().SetTitle("Signal Hits")
        grVFATNSignalNoBkg.GetYaxis().SetTitleOffset(1.5)
        grVFATNSignalNoBkg.GetYaxis().SetRangeUser(0,nTrig)
        grVFATNSignalNoBkg.GetXaxis().SetRangeUser(-0.5, nVFATS+0.5)
        grVFATNSignalNoBkg.Draw("APE1")
        canv_Signal.SaveAs(outputDir+'/SignalNoBkg.png')

    # Store - Sum over all VFATs
    canv_LatSum = r.TCanvas("canv_LatSumOverAllVFATs","canv_LatSumOverAllVFATs",600,600)
    canv_LatSum.cd()
    hHitsVsLat_AllVFATs.SetXTitle("Latency")
    hHitsVsLat_AllVFATs.SetYTitle("N")
    hHitsVsLat_AllVFATs.GetXaxis().SetRangeUser(latMin,latMax)
    hHitsVsLat_AllVFATs.Draw("hist")
    canv_LatSum.SaveAs(outputDir + '/LatSumOverAllVFATs.png')

    # Store - Max Hits By Lat Per VFAT
    canv_MaxHitsPerLatByVFAT = r.TCanvas("canv_MaxHitsPerLatByVFAT","canv_MaxHitsPerLatByVFAT",1200,600)
    canv_MaxHitsPerLatByVFAT.Divide(2,1)
    canv_MaxHitsPerLatByVFAT.cd(1)
    grNMaxLatBinByVFAT.SetTitle("")
    grNMaxLatBinByVFAT.SetMarkerStyle(21)
    grNMaxLatBinByVFAT.SetMarkerSize(0.7)
    grNMaxLatBinByVFAT.SetLineWidth(2)
    grNMaxLatBinByVFAT.GetXaxis().SetRangeUser(-0.5,nVFATS +0.5)
    grNMaxLatBinByVFAT.GetXaxis().SetTitle("VFAT Pos")
    grNMaxLatBinByVFAT.GetYaxis().SetRangeUser(0,nTrig)
    grNMaxLatBinByVFAT.GetYaxis().SetTitle("Hit Count of Max Lat Bin")
    grNMaxLatBinByVFAT.GetYaxis().SetTitleOffset(1.7)
    grNMaxLatBinByVFAT.Draw("APE1")
    canv_MaxHitsPerLatByVFAT.cd(2)
    grMaxLatBinByVFAT.SetTitle("")
    grMaxLatBinByVFAT.SetMarkerStyle(21)
    grMaxLatBinByVFAT.SetMarkerSize(0.7)
    grMaxLatBinByVFAT.SetLineWidth(2)
    grMaxLatBinByVFAT.GetXaxis().SetTitle("VFAT Pos")
    grMaxLatBinByVFAT.GetYaxis().SetTitle("Max Lat Bin")
    grMaxLatBinByVFAT.GetYaxis().SetTitleOffset(1.2)
    grMaxLatBinByVFAT.GetXaxis().SetRangeUser(-0.5,nVFATS+0.5)
    grMaxLatBinByVFAT.Draw("APE1")
    canv_MaxHitsPerLatByVFAT.SaveAs(outputDir+'/MaxHitsPerLatByVFAT.png')

    # Store - TObjects
    outF.cd()
    hHitsVsLat_AllVFATs.Write()
    grNMaxLatBinByVFAT.SetName("grNMaxLatBinByVFAT")
    grNMaxLatBinByVFAT.Write()
    grMaxLatBinByVFAT.SetName("grMaxLatBinByVFAT")
    grMaxLatBinByVFAT.Write()
    if performFit:
        grVFATSigOverBkg.SetName("grVFATSigOverBkg")
        grVFATSigOverBkg.Write()
        grVFATNSignalNoBkg.SetName("grVFATNSignalNoBkg")
        grVFATNSignalNoBkg.Write()
    myT.Write()
    outF.Close()
