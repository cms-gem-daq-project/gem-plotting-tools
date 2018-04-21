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
    from anautilities import first_index_gt
    from math import sqrt

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
   
    # Get list of bin edges in Y
    # Must be done for each VFAT since the conversion from DAC units to fC may be unique to the VFAT
    listOfBinEdgesY = {}
    for vfat in vfatHistos:
        listOfBinEdgesY[vfat] = [ vfatHistos[vfat].GetYaxis().GetBinLowEdge(binY) 
                for binY in range(1,vfatHistos[vfat].GetNbinsY()+2) ] #Include overflow
        
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
        
        # Determine the binY that corresponds to this charge value
        chargeBin = first_index_gt(listOfBinEdgesY[event.vfatN], charge)-1

        # Fill Summary Histogram 
        if lutType is mappingNames[1] and vfatHistosPanPin2 is not None:
            if (stripPinOrChan < 64):
                vfatHistos[event.vfatN].SetBinContent(63-(stripPinOrChan+1),chargeBin,event.Nhits)
                vfatHistos[event.vfatN].SetBinError(63-(stripPinOrChan+1),chargeBin,sqrt(event.Nhits))
                pass
            else:
                vfatHistosPanPin2[event.vfatN].SetBinContent(127-(stripPinOrChan+1),chargeBin,event.Nhits)
                vfatHistosPanPin2[event.vfatN].SetBinError(127-(stripPinOrChan+1),chargeBin,sqrt(event.Nhits))
                pass
            pass
        else:
            vfatHistos[event.vfatN].SetBinContent(stripPinOrChan+1,chargeBin,event.Nhits)
            pass

    return

def plotAllSCurvesOnCanvas(vfatHistos, vfatHistosPanPin2=None, obsName="scurves"):
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
        canv_dict[vfat] = r.TCanvas("canv_%s_vfat%i"%(obsName,vfat),"%s from VFAT%i"%(obsName,vfat),600,600)
        canv_dict[vfat].Draw()
        canv_dict[vfat].cd()
        for binX in range(1,histo.GetNbinsX()+1):
            h_scurve = histo.ProjectionY("h_%s_vfat%i_bin%i"%(obsName,vfat,binX),binX,binX,"")
            h_scurve.SetLineColor(r.kBlue+2)
            h_scurve.SetLineWidth(2)
            h_scurve.SetFillStyle(0)

            g_scurve = r.TGraph(h_scurve)
            if binX == 1:
                h_scurve.Draw()
            else:
                h_scurve.Draw("same")
        canv_dict[vfat].Update()
    if vfatHistosPanPin2 is not None:
        for vfat,histo in vfatHistosPanPin2.iteritems():
            canv_dict[vfat].cd()
            for binX in range(1,histo.GetNbinsX()+1):
                h_scurve = histo.ProjectionY("h_%s_vfat%i_bin%i"%(obsName,vfat,binX),binX,binX,"")
                h_scurve.SetLineColor(r.kBlue+2)
                h_scurve.SetLineWidth(2)
                h_scurve.SetFillStyle(0)
                h_scurve.Draw("same")

                g_scurve = r.TGraph(h_scurve)
            canv_dict[vfat].Update()

    return canv_dict

if __name__ == '__main__':
    import os
    import numpy as np
    import ROOT as r
    
    from array import array
    from anautilities import getEmptyPerVFATList, getMapping, isOutlierMADOneSided, parseCalFile, saveSummary, saveSummaryByiEta
    from anaInfo import mappingNames, MaskReason
    from fitting.fitScanData import ScanDataFitter
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import envCheck
    from mapping.chamberInfo import chamber_iEta2VFATPos, chamber_vfatPos2iEta

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

    from optparse import OptionGroup
    chanMaskGroup = OptionGroup(
            parser,
            "Options for channel mask decisions"
            "Parameters which specify how Dead, Noisy, and High Pedestal Channels are charaterized")
    chanMaskGroup.add_option("--maxEffPedPercent", type="float", dest="maxEffPedPercent", default=0.05,
                      help="Percentage, Threshold for setting the HighEffPed mask reason, if channel (effPed > maxEffPedPercent * nevts) then HighEffPed is set",
                      metavar="maxEffPedPercent")
    chanMaskGroup.add_option("--highNoiseCut", type="float", dest="highNoiseCut", default=1.0,
                      help="Threshold for setting the HighNoise maskReason, if channel (scurve_sigma > highNoiseCut) then HighNoise is set",
                      metavar="highNoiseCut")
    chanMaskGroup.add_option("--deadChanCutLow", type="float", dest="deadChanCutLow", default=4.14E-02,
                      help="If channel (deadChanCutLow < scurve_sigma < deadChanCutHigh) then DeadChannel is set",
                      metavar="deadChanCutLow")
    chanMaskGroup.add_option("--deadChanCutHigh", type="float", dest="deadChanCutHigh", default=1.09E-01,
                      help="If channel (deadChanCutHigh < scurve_sigma < deadChanCutHigh) then DeadChannel is set",
                      metavar="deadChanCutHigh")
    parser.add_option_group(chanMaskGroup)

    parser.set_defaults(outfilename="SCurveFitData.root")
    (options, args) = parser.parse_args()
    
    print("Analyzing: '%s'"%options.filename)
    filename = options.filename[:-5]
    os.system("mkdir " + filename)
    
    outfilename = options.outfilename
    GEBtype = options.GEBtype
   
    # Create the output File and TTree
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    if options.performFit:
        myT = r.TTree('scurveFitTree','Tree Holding FitData')

    tuple_calInfo = parseCalFile(options.calFile)
    calDAC2Q_Slope = tuple_calInfo[0]
    calDAC2Q_Intercept = tuple_calInfo[1]
    
    # Create output plot containers
    vSummaryPlots = ndict()
    vSummaryPlotsPanPin2 = ndict()
    vSummaryPlotsNoMaskedChan = ndict()
    vSummaryPlotsNoMaskedChanPanPin2 = ndict()
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
                'VFAT %i;Channels;VCal #left(fC#right)'%vfat,
                128,-0.5,127.5,256,
                calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
        vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsNoMaskedChan[vfat] = r.TH2D('vSummaryPlotsNoMaskedChan%i'%vfat,
                'VFAT %i;Channels;VCal #left(fC#right)'%vfat,
                128,-0.5,127.5,256,
                calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
        vSummaryPlotsNoMaskedChan[vfat].GetYaxis().SetTitleOffset(1.5)
        if not (options.channels or options.PanPin):
            vSummaryPlots[vfat].SetXTitle('Strip')
            vSummaryPlotsNoMaskedChan[vfat].SetXTitle('Strip')
            pass
        if options.PanPin:
            vSummaryPlots[vfat] = r.TH2D('vSummaryPlots%i'%vfat,
                    'VFAT %i_0-63;63 - Panasonic Pin;VCal #left(fC#right)'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoMaskedChan[vfat] = r.TH2D('vSummaryPlotsNoMaskedChan%i'%vfat,
                    'VFAT %i_0-63;63 - Panasonic Pin;VCal #left(fC#right)'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlotsNoMaskedChan[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsPanPin2[vfat] = r.TH2D('vSummaryPlotsPanPin2_%i'%vfat,
                    'vSummaryPlots%i_64-127;127 - Panasonic Pin;VCal #left(fC#right)'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlotsPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoMaskedChanPanPin2[vfat] = r.TH2D('vSummaryPlotsNoMaskedChanPanPin2_%i'%vfat,
                    'vSummaryPlots%i_64-127;127 - Panasonic Pin;VCal #left(fC#right)'%vfat,
                    64,-0.5,63.5,256,
                    calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat],
                    calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat])
            vSummaryPlotsNoMaskedChanPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
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
    nPulses = -1
    for event in inF.scurveTree:
        vthr_list[event.vfatN][event.vfatCH] = event.vthr
        trim_list[event.vfatN][event.vfatCH] = event.trimDAC
        trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
        
        # store event count
        if nPulses < 0:
            nPulses = event.Nev

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
        print("")
        masks = []
        maskReasons = []
        effectivePedestals = [ np.zeros(128) for vfat in range(0,24) ]
        print "| vfatN | Dead Chan | Hot Chan | Failed Fits | High Noise | High Eff Ped |"
        print "| :---: | :-------: | :------: | :---------: | :--------: | :----------: |"
        for vfat in range(0,24):
            trimValue = np.zeros(128)
            channelNoise = np.zeros(128)
            fitFailed = np.zeros(128, dtype=bool)
            for chan in range(0, 128):
                # Compute values for cuts
                channelNoise[chan] = scanFitResults[1][vfat][chan]
                effectivePedestals[vfat][chan] = fitter.scanFuncs[vfat][chan].Eval(0.0)
                
                # Compute the value to apply MAD on for each channel
                trimValue[chan] = scanFitResults[0][vfat][chan] - options.ztrim * scanFitResults[1][vfat][chan]
                pass
            fitFailed = np.logical_not(fitter.fitValid[vfat])
            
            # Determine outliers
            hot = isOutlierMADOneSided(trimValue, thresh=options.zscore,
                                       rejectHighTail=False)
            
            # Create reason array
            reason = np.zeros(128, dtype=int) # Not masked
            reason[hot] |= MaskReason.HotChannel
            reason[fitFailed] |= MaskReason.FitFailed
            nDeadChan = 0
            for chan in range(0,len(channelNoise)):
                if (options.deadChanCutLow < channelNoise[chan] and channelNoise[chan] < options.deadChanCutHigh):
                    reason[chan] |= MaskReason.DeadChannel
                    nDeadChan+=1
                    pass
                pass
            reason[channelNoise > options.highNoiseCut ] |= MaskReason.HighNoise
            nHighEffPed = 0
            for chan in range(0, len(effectivePedestals)):
                if chan not in fitter.Nev[vfat].keys():
                    continue
                if (effectivePedestals[vfat][chan] > (options.maxEffPedPercent * fitter.Nev[vfat][chan]) ):
                    reason[chan] |= MaskReason.HighEffPed
                    nHighEffPed+=1
                    pass
                pass
            maskReasons.append(reason)
            #masks.append(reason != MaskReason.NotMasked)
            masks.append((reason != MaskReason.NotMasked) * (reason != MaskReason.DeadChannel))
            print '| %i | %i | %i | %i | %i | %i |'%(
                    vfat,
                    nDeadChan,
                    np.count_nonzero(hot),
                    np.count_nonzero(fitFailed),
                    np.count_nonzero(channelNoise > options.highNoiseCut),
                    nHighEffPed)
    
    # Make Distributions w/o Hot Channels
    if options.performFit:
        print("Removing Hot Channels from Output Histograms")
        fill2DScurveSummaryPlots(
                scurveTree=inF.scurveTree, 
                vfatHistos=vSummaryPlotsNoMaskedChan, 
                vfatChanLUT=dict_vfatChanLUT, 
                vfatHistosPanPin2=vSummaryPlotsNoMaskedChanPanPin2, 
                lutType=stripChanOrPinType, 
                chanMasks=masks, 
                calDAC2Q_m=calDAC2Q_Slope, 
                calDAC2Q_b=calDAC2Q_Intercept)
    
    # Set the branches of the TTree and store the results
    if options.performFit:
        # Due to weird ROOT black magic this cannot be done here
        #myT = r.TTree('scurveFitTree','Tree Holding FitData')

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
        encSummaryPlots = {}
        encSummaryPlotsByiEta = {}
        fitSummaryPlots = {}
        effPedSummaryPlots = {}
        effPedSummaryPlotsByiEta = {}
        threshSummaryPlots = {}
        threshSummaryPlotsByiEta = {}
        allENC = np.zeros(3072)
        allENCByiEta = { ieta:np.zeros(3*128) for ieta in range(1,9) }
        allEffPed = -1.*np.ones(3072)
        allEffPedByiEta = { ieta:(-1.*np.ones(3*128)) for ieta in range(1,9) }
        allThresh = np.zeros(3072)
        allThreshByiEta = { ieta:np.zeros(3*128) for ieta in range(1,9) }
        
        for vfat in range(0,24):
            stripPinOrChanArray = np.zeros(128)
            for chan in range (0, 128):
                # Store stripChanOrPinType to use as x-axis of fit summary plots
                stripPinOrChan = dict_vfatChanLUT[vfat][stripChanOrPinType][chan]
                
                # Determine ieta
                ieta = chamber_vfatPos2iEta[vfat]
                iphi = chamber_iEta2VFATPos[ieta][vfat]

                # Store Values for making fit summary plots
                allENC[vfat*128 + chan] =  scanFitResults[1][vfat][chan]
                allEffPed[vfat*128 + chan] = effectivePedestals[vfat][chan]
                allThresh[vfat*128 + chan] = scanFitResults[0][vfat][chan]
                stripPinOrChanArray[chan] = float(stripPinOrChan)
                
                allENCByiEta[ieta][(iphi-1)*chan + chan] = scanFitResults[1][vfat][chan]
                allEffPedByiEta[ieta][(iphi-1)*chan + chan] = effectivePedestals[vfat][chan]
                allThreshByiEta[ieta][(iphi-1)*chan + chan] = scanFitResults[0][vfat][chan]

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
                    128,
                    stripPinOrChanArray,
                    allThresh[(vfat*128):((vfat+1)*128)],
                    np.zeros(128),
                    allENC[(vfat*128):((vfat+1)*128)]
                    )
            fitSummaryPlots[vfat].SetTitle("VFAT %i Fit Summary;Channel;Threshold #left(fC#right)"%vfat)
            
            if not (options.channels or options.PanPin):
                fitSummaryPlots[vfat].GetXaxis().SetTitle("Strip")
                pass
            elif options.PanPin:
                fitSummaryPlots[vfat].GetXaxis().SetTitle("Panasonic Pin")
                pass
            
            fitSummaryPlots[vfat].SetName("gFitSummary_VFAT%i"%(vfat))
            fitSummaryPlots[vfat].SetMarkerStyle(2)
            
            # Make thresh summary plot - bin size is variable
            thisVFAT_ThreshMean = np.mean(allThresh[(vfat*128):((vfat+1)*128)])
            thisVFAT_ThreshStd = np.std(allThresh[(vfat*128):((vfat+1)*128)])
            histThresh = r.TH1F("scurveMean_vfat%i"%vfat,"VFAT %i;S-Curve Mean #left(fC#right);N"%vfat,
                                40, thisVFAT_ThreshMean - 5. * thisVFAT_ThreshStd, thisVFAT_ThreshMean + 5. * thisVFAT_ThreshStd )
            histThresh.Sumw2()
            if thisVFAT_ThreshStd != 0: # Don't fill if we still at initial values
                for thresh in allThresh[(vfat*128):((vfat+1)*128)]:
                    if thresh == 0: # Skip the case where it still equals the inital value
                        continue
                    histThresh.Fill(thresh)
                    pass
                pass
            gThresh = r.TGraphErrors(histThresh)
            gThresh.SetName("gScurveMeanDist_vfat%i"%vfat)
            gThresh.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
            gThresh.GetYaxis().SetTitle("Entries / %f fC"%(thisVFAT_ThreshStd/4.))
            threshSummaryPlots[vfat] = gThresh

            # Make effective pedestal summary plot - bin size is fixed
            histEffPed = r.TH1F("scurveEffPed_vfat%i"%vfat,"VFAT %i;S-Curve Effective Pedestal #left(N#right);N"%vfat,
                                nPulses+1, -0.5, nPulses+0.5)
            histEffPed.Sumw2()
            for effPed in allEffPed[(vfat*128):((vfat+1)*128)]:
                if effPed < 0: # Skip the case where it still equals the inital value
                    continue
                histEffPed.Fill(effPed)
                pass
            pass
            histEffPed.SetMarkerStyle(21)
            histEffPed.SetMarkerColor(r.kRed)
            histEffPed.SetLineColor(r.kRed)
            #gEffPed = r.TGraphErrors(histEffPed)
            #gEffPed.SetName("gScurveEffPedDist_vfat%i"%vfat)
            #gEffPed.GetXaxis().SetTitle("scurve effective pedestal #left(N#right)")
            #gEffPed.GetYaxis().SetTitle("Entries / %f fC"%(thisVFAT_EffPedStd/4.))
            #effPedSummaryPlots[vfat] = gEffPed
            effPedSummaryPlots[vfat] = histEffPed
            
            # Make enc summary plot - bin size is variable
            thisVFAT_ENCMean = np.mean(allENC[(vfat*128):((vfat+1)*128)])
            thisVFAT_ENCStd = np.std(allENC[(vfat*128):((vfat+1)*128)])
            histENC = r.TH1F("scurveSigma_vfat%i"%vfat,"VFAT %i;S-Curve Sigma #left(fC#right);N"%vfat,
                                40, thisVFAT_ENCMean - 5. * thisVFAT_ENCStd, thisVFAT_ENCMean + 5. * thisVFAT_ENCStd )
            histENC.Sumw2()
            if thisVFAT_ENCStd != 0: # Don't fill if we are still at initial values
                for enc in allENC[(vfat*128):((vfat+1)*128)]:
                    if enc == 0: # Skip the case where it still equals the inital value
                        continue
                    histENC.Fill(enc)
                    pass
                pass
            gENC = r.TGraphErrors(histENC)
            gENC.SetName("gScurveSigmaDist_vfat%i"%vfat)
            gENC.GetXaxis().SetTitle("scurve sigma #left(fC#right)")
            gENC.GetYaxis().SetTitle("Entries / %f fC"%(thisVFAT_ENCStd/4.))
            encSummaryPlots[vfat] = gENC
            pass
  
        # Make a Thresh Summary Dist For the entire Detector
        detThresh_Mean = np.mean(allThresh[allThresh != 0]) #Don't consider intial values
        detThresh_Std = np.std(allThresh[allThresh != 0]) #Don't consider intial values
        hDetThresh_All = r.TH1F("hScurveMeanDist_All","All VFATs;S-Curve Mean #left(fC#right);N",
                            100, detThresh_Mean - 5. * detThresh_Std, detThresh_Mean + 5. * detThresh_Std )
        for thresh in allThresh[allThresh != 0]:
            hDetThresh_All.Fill(thresh)
            pass
        hDetThresh_All.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
        hDetThresh_All.GetYaxis().SetTitle("Entries / %f fC"%(detThresh_Std/10.))
        gDetThresh_All = r.TGraphErrors(hDetThresh_All)
        gDetThresh_All.SetName("gScurveMeanDist_All")
        gDetThresh_All.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
        gDetThresh_All.GetYaxis().SetTitle("Entries / %f fC"%(detThresh_Std/10.))

        # Make a EffPed Summary Dist For the entire Detector
        hDetEffPed_All = r.TH1F("hScurveEffPedDist_All","All VFATs;S-Curve Effective Pedestal #left(N#right);N",
                                nPulses+1, -0.5, nPulses+0.5)
        for effPed in allEffPed[allEffPed > -1]:
            hDetEffPed_All.Fill(effPed)
            pass
        hDetEffPed_All.GetXaxis().SetTitle("scurve effective pedestal #left(N#right)")
        hDetEffPed_All.GetYaxis().SetTitle("Entries")
        hDetEffPed_All.SetMarkerStyle(21)
        hDetEffPed_All.SetMarkerColor(r.kRed)
        hDetEffPed_All.SetLineColor(r.kRed)
        gDetEffPed_All = r.TGraphErrors(hDetEffPed_All)
        gDetEffPed_All.SetName("gScurveEffPedDist_All")
        gDetEffPed_All.GetXaxis().SetTitle("scurve effective pedestal #left(N#right)")
        gDetEffPed_All.GetYaxis().SetTitle("Entries")

        # Make a ENC Summary Dist For the entire Detector
        detENC_Mean = np.mean(allENC[allENC != 0]) #Don't consider intial values
        detENC_Std = np.std(allENC[allENC != 0]) #Don't consider intial values
        hDetENC_All = r.TH1F("hScurveSigmaDist_All","All VFATs;S-Curve Sigma #left(fC#right);N",
                            100, detENC_Mean - 5. * detENC_Std, detENC_Mean + 5. * detENC_Std )
        for enc in allENC[allENC != 0]:
            hDetENC_All.Fill(enc)
            pass
        hDetENC_All.GetXaxis().SetTitle("scurve sigma #left(fC#right)")
        hDetENC_All.GetYaxis().SetTitle("Entries / %f fC"%(detENC_Std/10.))
        gDetENC_All = r.TGraphErrors(hDetENC_All)
        gDetENC_All.SetName("gScurveSigmaDist_All")
        gDetENC_All.GetXaxis().SetTitle("scurve sigma #left(fC#right)")
        gDetENC_All.GetYaxis().SetTitle("Entries / %f fC"%(detENC_Std/10.))
    
        # Make the plots by iEta
        for ieta in range(1,9):
            # S-curve mean position (threshold)
            ietaThresh_Mean = np.mean(allThreshByiEta[ieta][allThreshByiEta[ieta] != 0])
            ietaThresh_Std = np.std(allThreshByiEta[ieta][allThreshByiEta[ieta] != 0])

            hThresh_iEta = r.TH1F(
                    "hScurveMeanDist_ieta%i"%(ieta),
                    "i#eta=%i;S-Curve Mean #left(fC#right);N"%(ieta),
                    80, 
                    ietaThresh_Mean - 5. * ietaThresh_Std, 
                    ietaThresh_Mean + 5. * ietaThresh_Std )
            
            for thresh in allThreshByiEta[ieta][allThreshByiEta[ieta] != 0]:
                hThresh_iEta.Fill(thresh)
                pass
            gThresh_iEta = r.TGraphErrors(hThresh_iEta)
            gThresh_iEta.SetName("gScurveMeanDist_ieta%i"%(ieta))
            gThresh_iEta.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
            gThresh_iEta.GetYaxis().SetTitle("Entries / %f fC"%(ietaThresh_Std/8.))
            threshSummaryPlotsByiEta[ieta] = gThresh_iEta

            # S-curve effective pedestal
            hEffPed_iEta = r.TH1F(
                    "hScurveEffPedDist_ieta%i"%(ieta),
                    "i#eta=%i;S-Curve Effective Pedestal #left(N#right);N"%(ieta),
                     nPulses+1, -0.5, nPulses+0.5)
            
            for effPed in allEffPedByiEta[ieta][allEffPedByiEta[ieta] > -1]:
                hEffPed_iEta.Fill(effPed)
                pass
            hEffPed_iEta.SetMarkerStyle(21)
            hEffPed_iEta.SetMarkerColor(r.kRed)
            hEffPed_iEta.SetLineColor(r.kRed)
            #gEffPed_iEta = r.TGraphErrors(hEffPed_iEta)
            #gEffPed_iEta.SetName("gScurveEffPedDist_ieta%i"%(ieta))
            #gEffPed_iEta.GetXaxis().SetTitle("scurve effective pedestal #left(fC#right)")
            #gEffPed_iEta.GetYaxis().SetTitle("Entries / %f fC"%(ietaEffPed_Std/8.))
            #effPedSummaryPlotsByiEta[ieta] = gEffPed_iEta
            effPedSummaryPlotsByiEta[ieta] = hEffPed_iEta

            # S-curve sigma (enc)
            ietaENC_Mean = np.mean(allENCByiEta[ieta][allENCByiEta[ieta] != 0])
            ietaENC_Std = np.std(allENCByiEta[ieta][allENCByiEta[ieta] != 0])

            hENC_iEta = r.TH1F(
                    "hScurveSigmaDist_ieta%i"%(ieta),
                    "i#eta=%i;S-Curve Sigma #left(fC#right);N"%(ieta),
                    80, 
                    ietaENC_Mean - 5. * ietaENC_Std, 
                    ietaENC_Mean + 5. * ietaENC_Std )
            
            for enc in allENCByiEta[ieta][allENCByiEta[ieta] != 0]:
                hENC_iEta.Fill(enc)
                pass
            gENC_iEta = r.TGraphErrors(hENC_iEta)
            gENC_iEta.SetName("gScurveSigmaDist_ieta%i"%(ieta))
            gENC_iEta.GetXaxis().SetTitle("scurve sigma pos #left(fC#right)")
            gENC_iEta.GetYaxis().SetTitle("Entries / %f fC"%(ietaENC_Std/8.))
            encSummaryPlotsByiEta[ieta] = gENC_iEta
            pass
        pass # end if options.performFit

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
            saveSummary(vSummaryPlotsNoMaskedChan, vSummaryPlotsNoMaskedChanPanPin2, '%s/PrunedSummary.png'%filename, trimVcal)
        else:
            saveSummary(vSummaryPlotsNoMaskedChan, None, '%s/PrunedSummary.png'%filename, trimVcal)
        saveSummary(fitSummaryPlots, None, '%s/fitSummary.png'%filename, None, drawOpt="APE1")
        saveSummary(threshSummaryPlots, None, '%s/ScurveMeanSummary.png'%filename, None, drawOpt="AP")
        saveSummary(effPedSummaryPlots, None, '%s/ScurveEffPedSummary.png'%filename, None, drawOpt="E1")
        saveSummary(encSummaryPlots, None, '%s/ScurveSigmaSummary.png'%filename, None, drawOpt="AP")

        saveSummaryByiEta(threshSummaryPlotsByiEta, '%s/ScurveMeanSummaryByiEta.png'%filename, None, drawOpt="AP")
        saveSummaryByiEta(effPedSummaryPlotsByiEta, '%s/ScurveEffPedSummaryByiEta.png'%filename, None, drawOpt="E1")
        saveSummaryByiEta(encSummaryPlotsByiEta, '%s/ScurveSigmaSummaryByiEta.png'%filename, None, drawOpt="AP")

        confF = open(filename+'/chConfig.txt','w')
        confF.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:mask/I:maskReason/I\n')
        for vfat in range(0,24):
            for chan in range (0, 128):
                confF.write('%i\t%i\t%i\t%i\t%i\t%i\n'%(
                    vfat,
                    dict_vfatID[vfat],
                    chan,
                    trim_list[vfat][chan],
                    masks[vfat][chan],
                    maskReasons[vfat][chan]))
                pass
            pass
        confF.close()
        pass

    # Make 1D Plot for each VFAT showing all scurves
    # Don't use the ones stored in fitter since this may not exist (e.g. options.performFit = false)
    canvOfScurveHistosNoMaskedChan = {}
    if options.PanPin:
        canvOfScurveHistos = plotAllSCurvesOnCanvas(vSummaryPlots,vSummaryPlotsPanPin2,"scurves")
    else:
        canvOfScurveHistos = plotAllSCurvesOnCanvas(vSummaryPlots,None,"scurves")

    if options.performFit:
        if options.PanPin:
            canvOfScurveHistosNoMaskedChan = plotAllSCurvesOnCanvas(vSummaryPlotsNoMaskedChan,vSummaryPlotsNoMaskedChanPanPin2,"scurvesNoMaskedChan")
        else:
            canvOfScurveHistosNoMaskedChan = plotAllSCurvesOnCanvas(vSummaryPlotsNoMaskedChan,None,"scurvesNoMaskedChan")
        
        canvOfScurveFits = {}
        for vfat in range(0,24):
            canvOfScurveFits[vfat] = r.TCanvas("canv_scurveFits_vfat%i"%vfat,"Scurve Fits from VFAT%i"%vfat,600,600)
            canvOfScurveFits[vfat].cd()
            for chan in range (0,128):
                if masks[vfat][chan]: # Do not draw fit for masked channels
                    continue

                if chan == 0:
                    fitter.scanFuncs[vfat][chan].Draw()
                else:
                    fitter.scanFuncs[vfat][chan].Draw("same")
            canvOfScurveFits[vfat].Update()

    # Save TObjects
    outF.cd()
    if options.performFit:
        myT.Write()
    for vfat in range(0,24):
        dirVFAT = outF.mkdir("VFAT%i"%vfat)
        dirVFAT.cd()
        vSummaryPlots[vfat].Write()
        if options.PanPin:
            vSummaryPlotsPanPin2[vfat].Write()
        canvOfScurveHistos[vfat].Write()
        if options.performFit:
            vSummaryPlotsNoMaskedChan[vfat].Write()
            if options.PanPin:
                vSummaryPlotsNoMaskedChanPanPin2[vfat].Write()
            fitSummaryPlots[vfat].Write()
            threshSummaryPlots[vfat].Write()
            effPedSummaryPlots[vfat].Write()
            encSummaryPlots[vfat].Write()
            canvOfScurveHistosNoMaskedChan[vfat].Write()
            canvOfScurveFits[vfat].Write()
            pass
    if options.performFit:
        dirSummary = outF.mkdir("Summary")
        dirSummary.cd()
        hDetThresh_All.Write()
        gDetThresh_All.Write()
        hDetEffPed_All.Write()
        gDetEffPed_All.Write()
        hDetENC_All.Write()
        gDetENC_All.Write()
   
        for ieta in range(1,9):
            dir_iEta = dirSummary.mkdir("ieta%i"%ieta)
            dir_iEta.cd()
            threshSummaryPlotsByiEta[ieta].Write()
            effPedSummaryPlotsByiEta[ieta].Write()
            encSummaryPlotsByiEta[ieta].Write()
            pass
        pass

    # Close output root file
    outF.Close()
