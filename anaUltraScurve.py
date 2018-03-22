#!/bin/env python

if __name__ = '__main__':
    import os
    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
    import ROOT as r
    
    from array import array
    from anautilities import getEmptyPerVFATList, getMapping
    from anaInfo import maskReason
    from fitting.fitScanData import ScanDataFitter
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import envCheck
    
    from anaoptions import parser
    parser.add_option("-b", "--drawbad", action="store_true", dest="drawbad",
                      help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")
    parser.add_option("--calFile", type="string", dest="calFile", default=None,
                      help="File specifying CAL_DAC/VCAL to fC equations per VFAT",
                      metavar="calFile")
    parser.add_option("-f", "--fit", action="store_true", dest="performFit",
                      help="Fit scurves and save fit information to output TFile", metavar="performFit")
    parser.add_option("--IsTrimmed", action="store_true", dest="IsTrimmed",
                      help="If the data is from a trimmed scan, plot the value it tried aligning to", metavar="IsTrimmed")
    parser.add_option("--zscore", type="float", dest="zscore", default=3.5,
                      help="Z-Score for Outlier Identification in MAD Algo", metavar="zscore")
    parser.add_option("--extChanMapping", type="string", dest="extChanMapping", default=None,
                      help="Physical filename of a custom, non-default, channel mapping (optional)", metavar="extChanMapping")
    parser.set_defaults(outfilename="SCurveFitData.root")
    (options, args) = parser.parse_args()
    
    print("Analyzing: '%s'"%filename)
    filename = options.filename[:-5]
    os.system("mkdir " + filename)
    
    outfilename = options.outfilename
    GEBtype = options.GEBtype
   
    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    # Build the channel to strip mapping from the text file
    envCheck('GEM_PLOTTING_PROJECT')
    projectHome = os.getenv('GEM_PLOTTING_PROJECT')
    dict_vfatChanLUT = ndict()
    if options.extChanMapping is not None:
        dict_vfatChanLUT = getMapping(options.extChanMapping)
    elif GEBtype == 'long':
        dict_vfatChanLUT = getMapping(projectHome+'/mapping/longChannelMap.txt', 'r')
    if GEBtype == 'short':
        dict_vfatChanLUT = getMapping(projectHome+'/mapping/shortChannelMap.txt', 'r')
   
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
    
    # Create the output File
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    myT = r.TTree('scurveFitTree','Tree Holding FitData')
    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vfatID = array( 'i', [-1] )
    myT.Branch( 'vfatID', vfatID, 'vfatID/I' ) #Hex Chip ID of VFAT
    vfatCH = array( 'i', [ 0 ] )
    myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    ROBstr = array( 'i', [ 0 ] )
    myT.Branch( 'ROBstr', ROBstr, 'ROBstr/I' )
    mask = array( 'i', [ 0 ] )
    myT.Branch( 'mask', mask, 'mask/I' )
    maskReason = array( 'i', [ 0 ] )
    myT.Branch( 'maskReason', maskReason, 'maskReason/I' )
    panPin = array( 'i', [ 0 ] )
    myT.Branch( 'panPin', panPin, 'panPin/I' )
    trimRange = array( 'i', [ 0 ] )
    myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
    vthr = array( 'i', [ 0 ] )
    myT.Branch( 'vthr', vthr, 'vthr/I' )
    trimDAC = array( 'i', [ 0 ] )
    myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
    threshold = array( 'f', [ 0 ] )
    myT.Branch( 'threshold', threshold, 'threshold/F')
    noise = array( 'f', [ 0 ] )
    myT.Branch( 'noise', noise, 'noise/F')
    pedestal = array( 'f', [ 0 ] )
    myT.Branch( 'pedestal', pedestal, 'pedestal/F')
    ped_eff = array( 'f', [ 0 ] )
    myT.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
    scurve_h = r.TH1D()
    myT.Branch( 'scurve_h', scurve_h)
    scurve_fit = r.TF1()
    myT.Branch( 'scurve_fit', scurve_fit)
    chi2 = array( 'f', [ 0 ] )
    myT.Branch( 'chi2', chi2, 'chi2/F')
    ndf = array( 'i', [ 0 ] )
    myT.Branch( 'ndf', ndf, 'ndf/I')
    Nhigh = array( 'i', [ 0 ] )
    myT.Branch( 'Nhigh', Nhigh, 'Nhigh/I')
    ztrim = array( 'f', [ 0 ] )
    ztrim[0] = options.ztrim
    myT.Branch( 'ztrim', ztrim, 'ztrim/F')
    
    # Create output plot containers
    vSummaryPlots = ndict()
    vSummaryPlotsPanPin2 = ndict()
    vSummaryPlotsNoHotChan = ndict()
    vSummaryPlotsNoHotChanPanPin2 = ndict()
    vScurves = getEmptyPerVFATList()
    vScurveFits = getEmptyPerVFATList()
    vthr_list = getEmptyPerVFATList() 
    trim_list = getEmptyPerVFATList() 
    trimrange_list = getEmptyPerVFATList()
    lines = []
    
    # Initialize distributions
    for vfat in range(0,24):
        if options.IsTrimmed:
            lines.append(r.TLine(-0.5, trimVcal[vfat], 127.5, trimVcal[vfat]))
            pass
        # vfat summary plots
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
            vScurves[vfat].append(r.TH1D('Scurve_%i_%i'%(vfat,chan),'Scurve_%i_%i;VCal [DAC units]'%(vfat,chan),256,-0.5,255.5))
            vScurveFits[vfat].append(r.TH1F())
            vthr_list[vfat].append(0)
            trim_list[vfat].append(0)
            trimrange_list[vfat].append(0)
            pass
        pass
    
    if options.SaveFile:
        fitter = ScanDataFitter()
        pass
    
    # Fill
    print("Filling Histograms")
    inF = r.TFile(filename+'.root')
    checkCurrentPulse = ("isCurrentPulse" in inF.scurveTree.GetListOfBranches())
    dict_calSF = dict((calSF, 0.25*calSF+0.25) for calSF in range(0,4))
    dict_vfatID = dict((vfat, 0) for vfat in range(0,24))
    listOfBranches = inF.scurveTree.GetListOfBranches()
    for event in inF.scurveTree:
        strip = chanToStripLUT[event.vfatN][event.vfatCH]
        pan_pin = chanToPanPinLUT[event.vfatN][event.vfatCH]
        charge = calDAC2Q_Slope[event.vfatN]*event.vcal+calDAC2Q_Intercept[event.vfatN]
        if checkCurrentPulse:
            if event.isCurrentPulse:
                #Q = CAL_DUR * CAL_DAC * 10nA * CAL_FS
                charge = (1./ 40079000) * event.vcal * (10 * 1e-9) * dict_calSF[event.calSF] * 1e15
        if not (options.channels or options.PanPin):
            vSummaryPlots[event.vfatN].Fill(strip,charge,event.Nhits)
            pass
        if options.channels:
            vSummaryPlots[event.vfatN].Fill(event.vfatCH,charge,event.Nhits)
            pass
        if options.PanPin:
            if (pan_pin < 64):
                vSummaryPlots[event.vfatN].Fill(63-pan_pin,charge,event.Nhits)
                pass
            else:
                vSummaryPlotsPanPin2[event.vfatN].Fill(127-pan_pin,charge,event.Nhits)
                pass
            pass
        
        binVal = vScurves[event.vfatN][event.vfatCH].FindBin(event.vcal)
        vScurves[event.vfatN][event.vfatCH].SetBinContent(binVal, event.Nhits)
        r.gStyle.SetOptStat(1111111)
        vthr_list[event.vfatN][event.vfatCH] = event.vthr
        trim_list[event.vfatN][event.vfatCH] = event.trimDAC
        trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
        
        if not (dict_vfatID[event.vfatN] > 0):
            if 'vfatID' in listOfBranches:
                dict_vfatID[event.vfatN] = event.vfatID
            else:
                dict_vfatID[event.vfatN] = 0
    
        if options.SaveFile:
            fitter.feed(event)
            pass
        pass
    
    if options.SaveFile:
        print("Fitting Histograms")
        fitSummary = open(filename+'/fitSummary.txt','w')
        fitSummary.write('vfatN/I:vfatID/I:vfatCH/I:fitP0/F:fitP1/F:fitP2/F:fitP3/F\n')
        scanFits = fitter.fit()
        for vfat in range(0,24):
            for chan in range(0,128):
                vScurveFits[vfat][chan]=fitter.getFunc(vfat,chan)
                fitSummary.write(
                        '%i\t%i\t%i\t%f\t%f\t%f\t%f\n'%(
                            vfat,
                            dict_vfatID[vfat],
                            chan,
                            vScurveFits[vfat][chan].GetParameter(0),
                            vScurveFits[vfat][chan].GetParameter(1),
                            vScurveFits[vfat][chan].GetParameter(2),
                            vScurveFits[vfat][chan].GetParameter(3)
                            )
                        )
        fitSummary.close()
        pass
    
    # Determine hot channels
    if options.SaveFile:
        print("Determining hot channels")
        masks = []
        maskReasons = []
        effectivePedestals = [ np.zeros(128) for vfat in range(24) ]
        for vfat in range(0, 24):
            trimValue = np.zeros(128)
            channelNoise = np.zeros(128)
            fitFailed = np.zeros(128, dtype=bool)
            for chan in range(0, 128):
                # Get fit results
                threshold[0] = scanFits[0][vfat][chan]
                noise[0] = scanFits[1][vfat][chan]
                pedestal[0] = scanFits[2][vfat][chan]
                
                # Compute values for cuts
                channelNoise[chan] = noise[0]
                effectivePedestals[vfat][chan] = vScurveFits[vfat][chan].Eval(0.0)
                
                # Compute the value to apply MAD on for each channel
                trimValue[chan] = threshold[0] - ztrim[0] * noise[0]
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
            print 'VFAT %2d: %d dead, %d hot channels, %d failed fits, %d high noise, %d high eff.ped.' % (vfat,
                    np.count_nonzero(fitter.isDead[vfat]),
                    np.count_nonzero(hot),
                    np.count_nonzero(fitFailed),
                    np.count_nonzero(channelNoise > 20),
                    np.count_nonzero(effectivePedestals[vfat] > 50))
    
    # Fill pruned
    if options.SaveFile:
        print("Pruning Hot Channels from Output Histograms")
        for event in inF.scurveTree:
            if masks[event.vfatN][event.vfatCH]:
                continue
            strip = chanToStripLUT[event.vfatN][event.vfatCH]
            pan_pin = chanToPanPinLUT[event.vfatN][event.vfatCH]
            charge = calDAC2Q_Slope[event.vfatN]*event.vcal+calDAC2Q_Intercept[event.vfatN]
            if checkCurrentPulse:
                if event.isCurrentPulse:
                    #Q = CAL_DUR * CAL_DAC * 10nA * CAL_FS
                    charge = (1./ 40079000) * event.vcal * (10 * 1e-9) * dict_calSF[event.calSF] * 1e15
            if not (options.channels or options.PanPin):
                vSummaryPlotsNoHotChan[event.vfatN].Fill(strip,charge,event.Nhits)
            if options.channels:
                vSummaryPlotsNoHotChan[event.vfatN].Fill(event.vfatCH,charge,event.Nhits)
            if options.PanPin:
                if (pan_pin < 64):
                    vSummaryPlotsNoHotChan[event.vfatN].Fill(63-pan_pin,charge,event.Nhits)
                else:
                    vSummaryPlotsNoHotChanPanPin2[event.vfatN].Fill(127-pan_pin,charge,event.Nhits)
    
    # Store values in ROOT file
    if options.SaveFile:
        print("Storing Output Data")
        fitSums = {}
        for vfat in range (0,24):
            fitThr = []        
            fitENC = []
            stripList = []
            panList = []
            chanList = []
            for chan in range (0, 128):
                # Get strip and pan pin
                strip = chanToStripLUT[vfat][chan]
                pan_pin = chanToPanPinLUT[vfat][chan]
                
                # Store strip, chan and pan pin
                stripList.append(float(strip))
                panList.append(float(pan_pin))
                chanList.append(float(chan))
                
                # Filling the Branches
                param0 = scanFits[0][vfat][chan]
                param1 = scanFits[1][vfat][chan]
                param2 = scanFits[2][vfat][chan]
                ped_eff[0] = effectivePedestals[vfat][chan]
                vfatN[0] = vfat
                vfatID[0] = dict_vfatID[vfat]
                vfatCH[0] = chan
                ROBstr[0] = strip
                panPin[0] = pan_pin
                trimRange[0] = trimrange_list[vfat][chan] 
                vthr[0] = vthr_list[vfat][chan]
                trimDAC[0] = trim_list[vfat][chan]
                threshold[0] = calDAC2Q_Slope[vfat]*param0+calDAC2Q_Intercept[vfat]
                fitThr.append(calDAC2Q_Slope[vfat]*param0+calDAC2Q_Intercept[vfat])
                noise[0] = calDAC2Q_Slope[vfat]*param1
                fitENC.append(calDAC2Q_Slope[vfat]*param1*ztrim[0])
                pedestal[0] = param2
                mask[0] = masks[vfat][chan]
                maskReason[0] = maskReasons[vfat][chan]
                chi2[0] = scanFits[3][vfat][chan]
                ndf[0] = int(scanFits[5][vfat][chan])
                holder_curve = vScurves[vfat][chan]
                holder_curve.Copy(scurve_h)
                scurve_fit = fitter.getFunc(vfat,chan).Clone('scurveFit_vfat%i_chan%i'%(vfat,chan))
                Nhigh[0] = int(scanFits[4][vfat][chan])
                
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
            if not (options.channels or options.PanPin):
                fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(stripList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
                fitSums[vfat].SetTitle("VFAT %i Fit Summary;Strip;Threshold [fC]"%vfat)
                pass
            elif options.channels:
                fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(chanList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
                fitSums[vfat].SetTitle("VFAT %i Fit Summary;Channel;Threshold [fC]"%vfat)
                pass
            elif options.PanPin:
                fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(panList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
                fitSums[vfat].SetTitle("VFAT %i Fit Summary;Panasonic Pin;Threshold [fC]"%vfat)
                pass
            
            fitSums[vfat].SetName("gFitSummary_VFAT%i"%(vfat))
            fitSums[vfat].SetMarkerStyle(2)
            pass
        pass
    
    def saveSummary(vSummaryPlots, vSummaryPlotsPanPin2, name='Summary'):
        legend = r.TLegend(0.75,0.7,0.88,0.88)
        r.gStyle.SetOptStat(0)
        if not options.PanPin:
            canv = make3x8Canvas('canv', vSummaryPlots, 'colz')
            for vfat in range(0,24):
                canv.cd(vfat+1)
                if options.IsTrimmed:
                    legend.Clear()
                    legend.AddEntry(line, 'trimVCal is %f'%(trimVcal[vfat]))
                    legend.Draw('SAME')
                    print trimVcal[vfat]
                    lines[vfat].SetLineColor(1)
                    lines[vfat].SetLineWidth(3)
                    lines[vfat].Draw('SAME')
                    pass
                canv.Update()
                pass
            pass
        else:
            canv = r.TCanvas('canv','canv',500*8,500*3)
            canv.Divide(8,6)
            r.gStyle.SetOptStat(0)
            for ieta in range(0,8):
                for iphi in range (0,3):
                    r.gStyle.SetOptStat(0)
                    canv.cd((ieta+1 + iphi*16)%48 + 16)
                    vSummaryPlots[ieta+(8*iphi)].Draw('colz')
                    canv.Update()
                    canv.cd((ieta+9 + iphi*16)%48 + 16)
                    vSummaryPlotsPanPin2[ieta+(8*iphi)].Draw('colz')
                    canv.Update()
                    pass
                pass
            pass
    
        canv.SaveAs(filename+'/%s.png' % name)
    
    saveSummary(vSummaryPlots, vSummaryPlotsPanPin2)
    if options.SaveFile:
        saveSummary(vSummaryPlotsNoHotChan, vSummaryPlotsNoHotChanPanPin2, name='PrunedSummary')
    
    if options.SaveFile:
        r.gStyle.SetOptStat(0)
        canv = make3x8Canvas('canv', fitSums, 'ap')
        canv.SaveAs(filename+'/fitSummary.png')
        pass
    
    if options.SaveFile:
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
        outF.cd()
        for vfat in fitSums.keys():
            fitSums[vfat].Write()
            pass
        myT.Write()
        outF.Close()
        pass
