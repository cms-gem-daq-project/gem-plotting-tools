#!/bin/env python

def fill2DScurveSummaryPlots(scurveTree, vfatHistos, vfatChanLUT, vfatHistosPanPin2=None, lutType="vfatCH", chanMasks=None, calDAC2Q_m=None, calDAC2Q_b=None):
    """
    Fills 2D Scurve summary plots from scurveTree TTree

    vfatHistos        - container of histograms for each vfat where len(vfatHistos) = Total number of VFATs
                        The n^th element is a 2D histogram of Hits vs. (Strip || Chan || PanPin)
    vfatChanLUT       - Nested dictionary specifying the VFAT channel to strip and PanPin mapping;
                        see getMapping() for details on expected format
    vfatHistosPanPin2 - As vfatHistos but for the other side of the readout board connector if lutType is "PanPin"
    lutType           - Type of look up to be peformed in vfatChanLUT, see mappingNames of anaInfo.py for
                        expected names
    chanMasks         - List of numpy arrays, one numpy array per vfat, elements of the numpy array
                        are expected to be ordered by VFAT channel number and correspond to 1 (0) for
                        (not) masked channel, optional parameter.
    calDAC2Q_m        - list of slope values for "fC = m * cal_dac + b" equation, ordered by vfat position
                        if argument is None a value of 1.0 is used for all VFATs
    calDAC2Q_b        - as calDAC2Q_m but for intercept b, but a value of 0 is used if argument is None
    """
    from anaInfo import dict_calSF, mappingNames

    # Check if lutType is expected
    if lutType not in mappingNames:
        print "fill2DScurveSummaryPlots() - lutType '%s' not supported"
        print "fill2DScurveSummaryPlots() - I was expecting one of the following: ", mappingNames
        raise LookupError

    # Set calDAC2Q slope to unity if not provided
    if calDAC2Q_m is None:
        calDAC2Q_m = np.ones(24)

    # Set calDAC2Q intercept to zero if not provided
    if calDAC2Q_b is None:
        calDAC2Q_b = np.zeros(24)
   
    # Fill Histograms
    checkCurrentPulse = ("isCurrentPulse" in scurveTree.GetListOfBranches())
    for event in scurveTree:
        if chanMasks is not None:
            if chanMasks[event.vfatN][event.vfatCH]:
                continue

        # Get the channel, strip, or Pan Pin
        stripPinOrChan = vfatChanLUT[event.vfatN][lutType][event.vfatCH]
        
        # Determine charge
        charge = calDAC2Q_m[event.vfatN]*event.vcal+calDAC2Q_b[event.vfatN]
        if checkCurrentPulse: #v3 electronics
            if event.isCurrentPulse:
                #Q = CAL_DUR * CAL_DAC * 10nA * CAL_FS
                charge = (1./ 40079000) * event.vcal * (10 * 1e-9) * dict_calSF[event.calSF] * 1e15
            else:
                charge = calDAC2Q_m[event.vfatN]*(256-event.vcal)+calDAC2Q_b[event.vfatN]
        
        # Fill Summary Histogram 
        if lutType is mappingNames[1] and vfatHistosPanPin2 is not None:
            if (stripPinOrChan < 64):
                vfatHistos[event.vfatN].Fill(63-stripPinOrChan,charge,event.Nhits)
                pass
            else:
                vfatHistosPanPin2[event.vfatN].Fill(127-stripPinOrChan,charge,event.Nhits)
                pass
            pass
        else:
            vfatHistos[event.vfatN].Fill(stripPinOrChan,charge,event.Nhits)

    return

def plotAllSCurvesOnCanvas(vfatHistos, vfatHistosPanPin2=None, obsName="canvScurves"):
    """
    Plots all scurves for a given vfat on a TCanvas for all vfats

    vfatHistos        - container of histograms for each vfat where len(vfatHistos) = Total number of VFATs
                        The n^th element is a 2D histogram of Hits vs. (Strip || Chan || PanPin)
    vfatHistosPanPin2 - As vfatHistos but for the other side of the readout board connector if lutType is "PanPin"
    obsName           - String to append the TCanvas created for each VFAT
    """
    import ROOT as r

    canv_dict = {}

    for vfat,histo in vfatHistos.iteritems():
        canv_dict[vfat] = r.TCanvas("%s_vfat%i"%(obsName,vfat),"%s from VFAT%i"%(obsName,vfat),600,600)
        canv_dict[vfat].cd()
        for binX in range(1,histo.GetNbinsX()+1):
            h_scurve = histo.ProjectionY("h_scurve",binX,binX,"")
            h_scurve.SetLineColor(r.kBlue+2)
            h_scurve.SetLineWidth(2)
            
            g_scurve = r.TGraph(h_scurve)
            if binX == 1:
                g_scurve.Draw("AP")
            else:
                g_scurve.Draw("sameP")
        canv_dict[vfat].Update()
    if vfatHistosPanPin2 is not None:
        for vfat,histo in vfatHistosPanPin2.iteritems():
            canv_dict[vfat].cd()
            for binX in range(1,histo.GetNbinsX()+1):
                h_scurve = histo.ProjectionY("h_scurve",binX,binX,"")
                h_scurve.SetLineColor(r.kBlue+2)
                h_scurve.SetLineWidth(2)
                
                g_scurve = r.TGraph(h_scurve)
                g_scurve.Draw("sameP")
            canv_dict[vfat].Update()

    return canv_dict

if __name__ == '__main__':
    import os
    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
    import ROOT as r
    
    from array import array
    from anautilities import getEmptyPerVFATList, getMapping, isOutlierMADOneSided, saveSummary
    from anaInfo import mappingNames, MaskReason
    from fitting.fitScanData import ScanDataFitter
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import envCheck
    
    from anaoptions import parser
    parser.add_option("-b", "--drawbad", action="store_true", dest="drawbad",
                      help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")
    parser.add_option("--calFile", type="string", dest="calFile", default=None,
                      help="File specifying CAL_DAC/VCAL to fC equations per VFAT",
                      metavar="calFile")
    parser.add_option("--extChanMapping", type="string", dest="extChanMapping", default=None,
                      help="Physical filename of a custom, non-default, channel mapping (optional)", metavar="extChanMapping")
    parser.add_option("-f", "--fit", action="store_true", dest="performFit",
                      help="Fit scurves and save fit information to output TFile", metavar="performFit")
    parser.add_option("--IsTrimmed", action="store_true", dest="IsTrimmed",
                      help="If the data is from a trimmed scan, plot the value it tried aligning to", metavar="IsTrimmed")
    parser.add_option("--zscore", type="float", dest="zscore", default=3.5,
                      help="Z-Score for Outlier Identification in MAD Algo", metavar="zscore")
    parser.set_defaults(outfilename="SCurveFitData.root")
    (options, args) = parser.parse_args()
    
    print("Analyzing: '%s'"%options.filename)
    filename = options.filename[:-5]
    os.system("mkdir " + filename)
    
    outfilename = options.outfilename
    GEBtype = options.GEBtype
   
    # Create the output File
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    
    # Set the CAL DAC to fC conversion
    calDAC2Q_Intercept = np.zeros(24)
    calDAC2Q_Slope = np.zeros(24)
    if options.calFile is not None:
        list_bNames = ["vfatN","slope","intercept"]
        calTree = r.TTree('calTree','Tree holding VFAT Calibration Info')
        calTree.ReadFile(options.calFile)
        array_CalData = rp.tree2array(tree=calTree, branches=list_bNames)
    
        for dataPt in array_CalData:
            calDAC2Q_Intercept[dataPt['vfatN']] = dataPt['intercept']
            calDAC2Q_Slope[dataPt['vfatN']] = dataPt['slope']
    else:
        calDAC2Q_Intercept = -0.8 * np.ones(24)
        calDAC2Q_Slope = 0.05 * np.ones(24)
    
    # Create output plot containers
    vSummaryPlots = ndict()
    vSummaryPlotsPanPin2 = ndict()
    vSummaryPlotsNoHotChan = ndict()
    vSummaryPlotsNoHotChanPanPin2 = ndict()
    vthr_list = getEmptyPerVFATList() 
    trim_list = getEmptyPerVFATList() 
    trimrange_list = getEmptyPerVFATList()
    
    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    # Initialize distributions
    for vfat in range(0,24):
        vSummaryPlots[vfat] = r.TH2D('vSummaryPlots%i'%vfat,
                'VFAT %i;Channels;VCal [fC]'%vfat,
                128,-0.5,127.5,256,
                calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
        vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsNoHotChan[vfat] = r.TH2D('vSummaryPlotsNoHotChan%i'%vfat,
                'VFAT %i;Channels;VCal [fC]'%vfat,
                128,-0.5,127.5,256,
                calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
        vSummaryPlotsNoHotChan[vfat].GetYaxis().SetTitleOffset(1.5)
        if not (options.channels or options.PanPin):
            vSummaryPlots[vfat].SetXTitle('Strip')
            vSummaryPlotsNoHotChan[vfat].SetXTitle('Strip')
            pass
        if options.PanPin:
            vSummaryPlots[vfat] = r.TH2D('vSummaryPlots%i'%vfat,
                    'VFAT %i_0-63;63 - Panasonic Pin;VCal [fC]'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoHotChan[vfat] = r.TH2D('vSummaryPlotsNoHotChan%i'%vfat,
                    'VFAT %i_0-63;63 - Panasonic Pin;VCal [fC]'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlotsNoHotChan[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsPanPin2[vfat] = r.TH2D('vSummaryPlotsPanPin2_%i'%vfat,
                    'vSummaryPlots%i_64-127;127 - Panasonic Pin;VCal [fC]'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlotsPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoHotChanPanPin2[vfat] = r.TH2D('vSummaryPlotsNoHotChanPanPin2_%i'%vfat,
                    'vSummaryPlots%i_64-127;127 - Panasonic Pin;VCal [fC]'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlotsNoHotChanPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
            pass
        for chan in range (0,128):
            vthr_list[vfat].append(0)
            trim_list[vfat].append(0)
            trimrange_list[vfat].append(0)
            pass
        pass
    
    # Determine chan, strip or panpin indep var
    stripChanOrPinType = mappingNames[2]
    if not (options.channels or options.PanPin):
        stripChanOrPinType = mappingNames[0]
    elif options.PanPin:
        stripChanOrPinType = mappingNames[1]

    # Build the channel to strip mapping from the text file
    envCheck('GEM_PLOTTING_PROJECT')
    projectHome = os.getenv('GEM_PLOTTING_PROJECT')
    dict_vfatChanLUT = ndict()
    if options.extChanMapping is not None:
        dict_vfatChanLUT = getMapping(options.extChanMapping)
    elif GEBtype == 'long':
        dict_vfatChanLUT = getMapping(projectHome+'/mapping/longChannelMap.txt')
    if GEBtype == 'short':
        dict_vfatChanLUT = getMapping(projectHome+'/mapping/shortChannelMap.txt')
   
    # Open the input ROOT File
    inF = r.TFile(filename+'.root')

    # Create the fitter
    checkCurrentPulse = ("isCurrentPulse" in inF.scurveTree.GetListOfBranches())
    if options.performFit:
        fitter = ScanDataFitter(
                calDAC2Q_m=calDAC2Q_Slope, 
                calDAC2Q_b=calDAC2Q_Intercept,
                isVFAT3=checkCurrentPulse,
                )
        pass

    # Get some of the operational settings of the ASIC
    # Refactor this using root_numpy???
    dict_vfatID = dict((vfat, 0) for vfat in range(0,24))
    listOfBranches = inF.scurveTree.GetListOfBranches()
    for event in inF.scurveTree:
        vthr_list[event.vfatN][event.vfatCH] = event.vthr
        trim_list[event.vfatN][event.vfatCH] = event.trimDAC
        trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
        
        # Store vfatID
        if not (dict_vfatID[event.vfatN] > 0):
            if 'vfatID' in listOfBranches:
                dict_vfatID[event.vfatN] = event.vfatID
            else:
                dict_vfatID[event.vfatN] = 0
        
        # Load the event into the fitter
        if options.performFit:
            fitter.feed(event)

    # Loop over input data and fill histograms
    print("Filling Histograms")
    fill2DScurveSummaryPlots(
            scurveTree=inF.scurveTree, 
            vfatHistos=vSummaryPlots, 
            vfatChanLUT=dict_vfatChanLUT, 
            vfatHistosPanPin2=vSummaryPlotsPanPin2, 
            lutType=stripChanOrPinType, 
            chanMasks=None, 
            calDAC2Q_m=calDAC2Q_Slope, 
            calDAC2Q_b=calDAC2Q_Intercept)
    
    if options.performFit:
        # Fit Scurves        
        print("Fitting Histograms")
        fitSummary = open(filename+'/fitSummary.txt','w')
        fitSummary.write('vfatN/I:vfatID/I:vfatCH/I:fitP0/F:fitP1/F:fitP2/F:fitP3/F\n')
        scanFitResults = fitter.fit()
        for vfat in range(0,24):
            for chan in range(0,128):
                fitSummary.write(
                        '%i\t%i\t%i\t%f\t%f\t%f\t%f\n'%(
                            vfat,
                            dict_vfatID[vfat],
                            chan,
                            fitter.scanFuncs[vfat][chan].GetParameter(0),
                            fitter.scanFuncs[vfat][chan].GetParameter(1),
                            fitter.scanFuncs[vfat][chan].GetParameter(2),
                            fitter.scanFuncs[vfat][chan].GetParameter(3)
                            )
                        )
        fitSummary.close()
    
        # Determine hot channels
        print("Determining hot channels")
        masks = []
        maskReasons = []
        effectivePedestals = [ np.zeros(128) for vfat in range(24) ]
        print "| vfatN | Dead Chan | Hot Chan | Failed Fits | High Noise | High Eff Ped |"
        print "| :---: | :-------: | :------: | :---------: | :--------: | :----------: |"
        for vfat in range(0, 24):
            trimValue = np.zeros(128)
            channelNoise = np.zeros(128)
            fitFailed = np.zeros(128, dtype=bool)
            for chan in range(0, 128):
                # Compute values for cuts
                channelNoise[chan] = scanFitResults[1][vfat][chan]
                effectivePedestals[vfat][chan] = fitter.scanFuncs[vfat][chan].Eval(0.0)
                
                # Compute the value to apply MAD on for each channel
                trimValue[chan] = scanFitResults[0][vfat][chan] - ztrim[0] * scanFitResults[1][vfat][chan]
                pass
            fitFailed = np.logical_not(fitter.fitValid[vfat])
            
            # Determine outliers
            hot = isOutlierMADOneSided(trimValue, thresh=options.zscore,
                                       rejectHighTail=False)
            
            # Create reason array
            reason = np.zeros(128, dtype=int) # Not masked
            reason[hot] |= MaskReason.HotChannel
            reason[fitFailed] |= MaskReason.FitFailed
            reason[fitter.isDead[vfat]] |= MaskReason.DeadChannel
            reason[channelNoise > 20] |= MaskReason.HighNoise
            reason[effectivePedestals[vfat] > 50] |= MaskReason.HighEffPed
            maskReasons.append(reason)
            masks.append(reason != MaskReason.NotMasked)
            print '| %i | %i | %i | %i | %i | %i |'%(
                    vfat,
                    np.count_nonzero(fitter.isDead[vfat]),
                    np.count_nonzero(hot),
                    np.count_nonzero(fitFailed),
                    np.count_nonzero(channelNoise > 20),
                    np.count_nonzero(effectivePedestals[vfat] > 50))
    
    # Make Distributions w/o Hot Channels
    if options.performFit:
        print("Removing Hot Channels from Output Histograms")
        fill2DScurveSummaryPlots(
                scurveTree=inF.scurveTree, 
                vfatHistos=vSummaryPlotsNoHotChan, 
                vfatChanLUT=dict_vfatChanLUT, 
                vfatHistosPanPin2=vSummaryPlotsNoHotChanPanPin2, 
                lutType=stripChanOrPinType, 
                chanMasks=masks, 
                calDAC2Q_m=calDAC2Q_Slope, 
                calDAC2Q_b=calDAC2Q_Intercept)
    
    # Create the output TTree and store the results
    if options.performFit:
        myT = r.TTree('scurveFitTree','Tree Holding FitData')

        chi2 = array( 'f', [ 0 ] )
        myT.Branch( 'chi2', chi2, 'chi2/F')
        mask = array( 'i', [ 0 ] )
        myT.Branch( 'mask', mask, 'mask/I' )
        maskReason = array( 'i', [ 0 ] )
        myT.Branch( 'maskReason', maskReason, 'maskReason/I' )
        ndf = array( 'i', [ 0 ] )
        myT.Branch( 'ndf', ndf, 'ndf/I')
        Nhigh = array( 'i', [ 0 ] )
        myT.Branch( 'Nhigh', Nhigh, 'Nhigh/I')
        noise = array( 'f', [ 0 ] )
        myT.Branch( 'noise', noise, 'noise/F')
        panPin = array( 'i', [ 0 ] )
        myT.Branch( 'panPin', panPin, 'panPin/I' )
        pedestal = array( 'f', [ 0 ] )
        myT.Branch( 'pedestal', pedestal, 'pedestal/F')
        ped_eff = array( 'f', [ 0 ] )
        myT.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
        ROBstr = array( 'i', [ 0 ] )
        myT.Branch( 'ROBstr', ROBstr, 'ROBstr/I' )
        trimDAC = array( 'i', [ 0 ] )
        myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
        threshold = array( 'f', [ 0 ] )
        myT.Branch( 'threshold', threshold, 'threshold/F')
        trimRange = array( 'i', [ 0 ] )
        myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
        vfatCH = array( 'i', [ 0 ] )
        myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
        vfatID = array( 'i', [-1] )
        myT.Branch( 'vfatID', vfatID, 'vfatID/I' ) #Hex Chip ID of VFAT
        vfatN = array( 'i', [ 0 ] )
        myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
        vthr = array( 'i', [ 0 ] )
        myT.Branch( 'vthr', vthr, 'vthr/I' )
        scurve_h = r.TH1F()
        myT.Branch( 'scurve_h', scurve_h)
        scurve_fit = r.TF1()
        myT.Branch( 'scurve_fit', scurve_fit)
        ztrim = array( 'f', [ 0 ] )
        ztrim[0] = options.ztrim
        myT.Branch( 'ztrim', ztrim, 'ztrim/F')
    
        print("Storing Output Data")
        fitSummaryPlots = {}
        threshSummaryPlots = {}
        encSummaryPlots = {}
        for vfat in range (0,24):
            fitThr = np.zeroes(128)        
            fitENC = np.zeroes(128)
            stripPinOrChanArray = np.zeroes(128)
            for chan in range (0, 128):
                # Store stripChanOrPinType to use as x-axis of fit summary plots
                stripPinOrChan = float( dict_vfatChanLUT[vfat][stripChanOrPinType][chan] )
               
                # Store Values for making fit summary plots
                fitThr[stripPinOrChan] = scanFitResults[0][vfat][chan]
                fitENC[stripPinOrChan] = scanFitResults[1][vfat][chan]
                stripPinOrChanArray[stripPinOrChan] = float(stripPinOrChan)

                # Set arrays linked to TBranches
                chi2[0] = scanFitResults[3][vfat][chan]
                mask[0] = masks[vfat][chan]
                maskReason[0] = maskReasons[vfat][chan]
                ndf[0] = int(scanFitResults[5][vfat][chan])
                Nhigh[0] = int(scanFitResults[4][vfat][chan])
                noise[0] = scanFitResults[1][vfat][chan]
                panPin[0] = dict_vfatChanLUT[vfat]["PanPin"][chan] 
                ped_eff[0] = effectivePedestals[vfat][chan]
                pedestal[0] = scanFitResults[2][vfat][chan]
                ROBstr[0] = dict_vfatChanLUT[vfat]["Strip"][chan]
                threshold[0] = scanFitResults[0][vfat][chan]
                trimDAC[0] = trim_list[vfat][chan]
                trimRange[0] = trimrange_list[vfat][chan] 
                vfatCH[0] = chan
                vfatID[0] = dict_vfatID[vfat]
                vfatN[0] = vfat
                vthr[0] = vthr_list[vfat][chan]
                
                # Set TObjects linked to TBranches
                holder_curve = fitter.scanHistos[vfat][chan]
                holder_curve.Copy(scurve_h)
                scurve_fit = fitter.getFunc(vfat,chan).Clone('scurveFit_vfat%i_chan%i'%(vfat,chan))
                
                # Filling the arrays for plotting later
                if options.drawbad:
                    if (chi2[0] > 1000.0 or chi2[0] < 1.0):
                        canvas = r.TCanvas('canvas', 'canvas', 500, 500)
                        r.gStyle.SetOptStat(1111111)
                        scurve_h.Draw()
                        scurve_fit.Draw('SAME')
                        canvas.Update()
                        canvas.SaveAs('Fit_Overlay_vfat%i_vfatCH%i.png'%(VFAT, chan))
                        pass
                    pass
                myT.Fill()
                pass

            # Make fit Summary plot
            fitSummaryPlots[vfat] = r.TGraphErrors(
                    len(fitThr),
                    stripPinOrChanArray,
                    fitThr,
                    len(fitThr),
                    fitENC
                    )
            fitSummaryPlots[vfat].SetTitle("VFAT %i Fit Summary;Channel;Threshold [fC]"%vfat)
            
            if not (options.channels or options.PanPin):
                fitSummaryPlots[vfat].GetXaxis().SetTitle("Strip")
                pass
            elif options.PanPin:
                fitSummaryPlots[vfat].GetXaxis().SetTitle("Panasonic Pin")
                pass
            
            fitSummaryPlots[vfat].SetName("gFitSummary_VFAT%i"%(vfat))
            fitSummaryPlots[vfat].SetMarkerStyle(2)
            
            # Make thresh summary plot - bin size is variable
            histThresh = r.TH1F("scurveMean_vfat%i"%vfat,"VFAT %i;S-Curve Mean #left(fC#right);N"%vfat,
                                100, np.mean(fitThr) - 5. * np.std(fitThr), np.mean(fitThr) + 5. * np.std(fitThr) )
            histThresh.Sumw2()
            for thresh in fitThr:
                histThresh.Fill(thresh)
            gThresh = r.TGraphErrors(histThresh)
            gThresh.SetName("gScurveMeanDist_vfat%i"%vfat)
            threshSummaryPlots[vfat] = gThresh

            # Make enc summary plot - bin size is variable
            histENC = r.TH1F("scurveSigma_vfat%i"%vfat,"VFAT %i;S-Curve Sigma #left(fC#right);N"%vfat,
                                100, np.mean(fitENC) - 5. * np.std(fitENC), np.mean(fitENC) + 5. * np.std(fitENC) )
            histENC.Sumw2()
            for enc in fitENC:
                histENC.Fill(enc)
            gENC = r.TGraphErrors(histENC)
            gENC.SetName("gScurveSigmaDist_vfat%i"%vfat)
            encSummaryPlots[vfat] = gThresh
            pass
        pass
   
    # Check if inputfile is trimmed
    trimVcal = None
    if options.IsTrimmed:
        trimmed_text = open('scanInfo.txt', 'r')
        trimVcal = []
        for vfat in range(0,24):
            trimVcal.append(0)
            pass
        for n, line in enumerate(trimmed_text):
            if n == 0: continue
            print line
            scanInfo = line.rsplit('  ')
            trimVcal[int(scanInfo[0])] = float(scanInfo[4])
            pass
        pass
    
    # Save the summary plots and channel config file
    if options.PanPin:
        saveSummary(vSummaryPlots, vSummaryPlotsPanPin2, '%s/Summary.png'%filename, trimVcal) 
    else: 
        saveSummary(vSummaryPlots, None, '%s/Summary.png'%filename, trimVcal)

    if options.performFit:
        if options.PanPin:
            saveSummary(vSummaryPlotsNoHotChan, vSummaryPlotsNoHotChanPanPin2, '%s/PrunedSummary.png'%filename, trimVcal)
        else:
            saveSummary(vSummaryPlotsNoHotChan, None, '%s/PrunedSummary.png'%filename, trimVcal)
        saveSummary(fitSummaryPlots, None, '%s/fitSummary.png'%filename, None)
        saveSummary(threshSummaryPlots, None, '%s/ScurveMeanSummary.png'%filename, None)
        saveSummary(encSummaryPlots, None, '%s/ScurveWidthSummary.png'%filename, None)

        confF = open(filename+'/chConfig.txt','w')
        confF.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:mask/I\n')
        for vfat in range (0,24):
            for chan in range (0, 128):
                confF.write('%i\t%i\t%i\t%i\t%i\n'%(
                    vfat,
                    dict_vfatID[vfat],
                    chan,
                    trim_list[vfat][chan],
                    masks[vfat][chan]))
                pass
            pass
        confF.close()
        pass

    # Make 1D Plot for each VFAT showing all scurves
    # Don't use the ones stored in fitter since this may not exist (e.g. options.performFit = false)
    if options.PanPin:
        canvOfScurveHistos = plotAllSCurvesOnCanvas(vSummaryPlots,vSummaryPlotsPanPin2,"canvScurves")
    else:
        canvOfScurveHistos = plotAllSCurvesOnCanvas(vSummaryPlots,None,"canvScurves")

    if options.performFit:
        if options.PanPin:
            canvOfScurveHistosNoHotChan = plotAllSCurvesOnCanvas(vSummaryPlotsNoHotChan,vSummaryPlotsNoHotChanPanPin2,"canvScurvesNotHotChan")
        else:
            canvOfScurveHistosNoHotChan = plotAllSCurvesOnCanvas(vSummaryPlotsNoHotChan,None,"canvScurvesNoHotChan")
        
        canvOfScurveFits = {}
        for vfat in range(0,24):
            canvOfScurveFits[vfat] = r.TCanvas("canvScurveFits_vfat%i"%vfat,"Scurve Fits from VFAT%i"%vfat,600,600)
            canvOfScurveFits[vfat].cd()
            for chan in range (0,128):
                if chan == 0:
                    fitter.scanFuncs[vfat][ch].Draw()
                else:
                    fitter.scanFuncs[vfat][ch].Draw("same")
            canvOfScurveFits[vfat].Update()

    # Save TObjects
    outF.cd()
    if options.performFit:
        myT.Write()
    for vfat in range(0,23):
        dirVFAT = outF.mkdir("VFAT%i"%vfat)
        dirVFAT.cd()
        vSummaryPlots[vfat].Write()
        if options.PanPin:
            vSummaryPlotsPanPin2.Write()
        canvOfScurveHistos[vfat].Write()
        if options.performFit:
            vSummaryPlotsNoHotChan.Write()
            if options.PanPin:
                vSummaryPlotsNoHotChanPanPin2.Write()
            fitSummaryPlots[vfat].Write()
            threshSummaryPlots[vfat].Write()
            encSummaryPlots[vfat].Write()
            canvOfScurveHistosNoHotChan[vfat].Write()
            canvOfScurveFits[vfat].Write()
            pass
    
    # Close output root file
    outF.Close()
