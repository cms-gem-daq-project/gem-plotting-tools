r"""
``scurveAlgos`` --- Utilities for analyzing scurve scan data
============================================================

.. code-block:: python

    import gempython.gemplotting.utils.scurveAlgos

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Utilities for analyzing scurve scan data

Documentation
-------------
"""

def anaUltraScurveStar(inputs):
    """
    Wrapper to be used with multiprocessing.Pool methods
    See: https://stackoverflow.com/questions/5442910/python-multiprocessing-pool-map-for-multiple-arguments
    
    When moving to python 3.X we should use the Pool::starmap function and not this wrapper:
    see: https://stackoverflow.com/a/5442981
    """
    return anaUltraScurve(*inputs)

def anaUltraScurve(args, scurveFilename, calFile=None, GEBtype="short", outputDir=None, vfatList=None):
    """
    Performs the scurve analysis on the input scurve TFile scurveFilename containing the scurveTree TTree.  The args namespace is expected to have the following attributes.  
    If this is called by a child process sys.stdout will be overwritten and be "outputDir/anaLog.log" if outputDir is not None or "$ELOG_PATH/anaLog.log" if outputDir is None.  If this is called by the MainProcess no changes to sys.stdout will be made.

    calFile - None or string that is the filename of a file specifying the conversion between CFG_CAL_DAC or VCal to fC. If None this will attempt to perform a DB query based on stored chipID in input scurveTree
    channels - If true output plots are made vs. vfatCH
    deadChanCutLow - Lower bound of charge range (in fC) that will be used to determine if a channel is dead based on its ENC
    deadChanCutHigh - Higher bound of charge range (in fC) that will be used to determine if a channel is dead based on its ENC
    debug - If true additional debugging information will be printed
    doNotFit - If true the scurves will not be fit; this will reduce the analysis tiem and output information
    drawbad - If true scurve fits with chi2 values less than 1 or greater than 1000 will be drawn on a separate TCanvas
    extChanMapping - Name of externally supplied file that specifies the ROBstr:PanPin:vfatCH mapping
    isVFAT2 - If true the data is understood as coming from VFAT2
    PanPin - If true output plots are made vs. PanPin
    outfilename - Name of outputfilename that will be used
    
    Returns a structured numpy array with the following dnames 
        
        ['mask','maskReason','noise','pedestal','ped_eff','threshold','vfatCH','vfatID','vfatN']

    Other arguments are:
    
    calFile - calibration file specifying the CFG_CAL_DAC conversion per VFAT to charge units; if None a DB query will be performed in an attempt to determine this info based on the stored 'vfatID' branch of the input scurveTree
    GEBtype - The detector type being analyzed
    outputDir - Directory where output plots are stored.  If None this will be default to $ELOG_PATH 
    vfatList - List of VFAT positions to consider in the analysis, if None analyzes all (default). Useful for debugging
    """
        # Check attributes of input args
    # If not present assign appropriate default arguments
    if hasattr(args,'calFile') is False:
        args.calFile = None
    if hasattr(args,'channels') is False:
        args.channels = False
    if hasattr(args,'deadChanCutLow') is False:
        args.deadChanCutLow = None
    if hasattr(args,'deadChanCutHigh') is False:
        args.deadChanCutHigh = None
    if hasattr(args,'debug') is False:
        args.debug = False
    if hasattr(args,'doNotFit') is False:
        args.doNotFit = False
    if hasattr(args,'drawbad') is False:
        args.drawbad = False
    if hasattr(args,'extChanMapping') is False:
        args.extChanMapping = None
    if hasattr(args,'isVFAT2') is False:
        args.isVFAT2 = False
    if hasattr(args,'PanPin') is False:
        args.PanPin = False
    if hasattr(args, 'outfilename') is False:
        args.outfilename = "SCurveFitData.root"

    #Get Defaults
    isVFAT3 = (not args.isVFAT2)
    performFit = (not args.doNotFit)
    outfilename = args.outfilename
    if outputDir is None:
        from gempython.gemplotting.utils.anautilities import getElogPath
        outputDir = getElogPath()
        pass

    # Redirect sys.stdout and sys.stderr if necessary 
    from gempython.gemplotting.utils.multiprocUtils import redirectStdOutAndErr
    redirectStdOutAndErr("anaUltraScurve",outputDir)
    
    if args.isVFAT2: #if isVFAT2, deadChanCut are set to default for v2 electronics
        dacName = "VCal"
        if args.deadChanCutLow is None:
            args.deadChanCutLow = 4.14E-02
        if args.deadChanCutHigh is None:
            args.deadChanCutHigh = 1.09E-01
    else: #if isVFAT3, deadChanCut are set to default for v3 electronics
        dacName = "CFG_CAL_DAC"
        if args.deadChanCutLow is None:
            # FIXME with HV3b_V3 hybrids simple rectangular cut is not possible
            #args.deadChanCutLow = 1.0E-02
            args.deadChanCutLow = 0
        if args.deadChanCutHigh is None:
            # FIXME with HV3b_V3 hybrids simple rectangular cut is not possible
            #args.deadChanCutHigh = 5.0E-01
            args.deadChanCutHigh = 0
   
    # Create the output File and TTree
    import ROOT as r
    outF = r.TFile(outputDir+'/'+outfilename, 'recreate')
    if not outF.IsOpen():
        outF.Close()
        raise IOError("Unable to open output file {1} check to make sure you have write permissions under {0}".format(outputDir,outfilename))
    if outF.IsZombie():
        outF.Close()
        raise IOError("Output file {1} is a Zombie, check to make sure you have write permissions under {0}".format(outputDir,outfilename))
    scurveFitTree = r.TTree('scurveFitTree','Tree Holding FitData')
    
    # Attempt to open input TFile
    inFile = r.TFile(scurveFilename,'read')
    if not inFile.IsOpen():
        outF.Close()
        inFile.Close()
        raise IOError("Unable to open input file {0} check to make sure you have read permissions".format(scurveFilename))
    if inFile.IsZombie():
        outF.Close()
        inFile.Close()
        raise IOError("Input file {0} is a Zombie, check to make sure you have write permissions and file has expected size".format(scurveFilename))
    scurveTree = inFile.scurveTree

    # Get ChipID's
    import numpy as np
    import root_numpy as rp
    ##### FIXME
    from gempython.gemplotting.mapping.chamberInfo import gemTypeMapping
    if 'gemType' not in inFile.scurveTree.GetListOfBranches():
        gemType = "ge11"
    else:
        gemType = gemTypeMapping[rp.tree2array(tree=inFile.scurveTree, branches =[ 'gemType' ] )[0][0]]
    print gemType
    ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans

    if ((vfatList is not None) and ((min(vfatList) < 0) or (max(vfatList) > nVFATS-1))):
        raise ValueError("anaUltraScurve(): Either vfatList=None or entries in vfatList must be in [0,{0}]".format(nVFATS-1))
    
    listOfBranches = scurveTree.GetListOfBranches()
    if 'vfatID' in listOfBranches:
        array_chipID = np.unique(rp.tree2array(scurveTree, branches = [ 'vfatID','vfatN' ] ))
        dict_chipID = {}
        for entry in array_chipID:
            dict_chipID[entry['vfatN']]=entry['vfatID']
    else:
        dict_chipID = { vfat:0 for vfat in range(nVFATS) }
        

        
    if args.debug:
        print("VFAT Position to ChipID Mapping")
        for vfat,vfatID in dict_chipID.iteritems():
            print(vfat,vfatID)
   
    # Get Nevts
    nevts = np.asscalar(np.unique(rp.tree2array(scurveTree, branches = [ 'Nev' ] )))[0] # for some reason numpy returns this as a tuple...
    
    # Determine CAL DAC calibration
    from gempython.utils.gemlogger import printYellow
    if args.calFile is None:
        printYellow("Calibration info for {0} taken from DB Query".format(dacName))
        from gempython.gemplotting.utils.dbutils import getVFAT3CalInfo
        # Need to pass a list to getVFAT3CalInfo() where idx of list matches vfatN
        if len(dict_chipID) != nVFATS:
            for vfat in range(nVFATS):
                if vfat not in dict_chipID:
                    dict_chipID[vfat] = -1
        dbInfo = getVFAT3CalInfo(dict_chipID.values(), debug=args.debug)
        calDAC2Q_Slope = dbInfo['cal_dacm']
        calDAC2Q_Intercept = dbInfo['cal_dacb']
    else:
        printYellow("Calibration info for {0} taken from input file: {1}".format(dacName,args.calFile))
        from gempython.gemplotting.utils.anautilities import parseCalFile
        tuple_calInfo = parseCalFile(args.calFile, gemType)
        calDAC2Q_Slope = tuple_calInfo[0]
        calDAC2Q_Intercept = tuple_calInfo[1]

    # Create output plot containers
    from gempython.utils.nesteddict import nesteddict as ndict
    vSummaryPlots = ndict()
    vSummaryPlotsPanPin2 = ndict()
    vSummaryPlotsNoMaskedChan = ndict()
    vSummaryPlotsNoMaskedChanPanPin2 = ndict()

    from gempython.gemplotting.utils.anautilities import getEmptyPerVFATList
    vthr_list = getEmptyPerVFATList(nVFATS) 
    trim_list = getEmptyPerVFATList(nVFATS) 
    trimRange_list = getEmptyPerVFATList(nVFATS)
    trimPolarity_list = getEmptyPerVFATList(nVFATS)
    
    # Set default histogram behavior
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)
    
    # Determine chan, strip or panpin indep var
    from gempython.gemplotting.utils.anaInfo import mappingNames
    if ((not args.channels) and (not args.PanPin)):
        stripChanOrPinName = ("ROBstr","Strip")
        stripChanOrPinType = mappingNames[0]
    elif args.channels:
        stripChanOrPinType = mappingNames[2]
        stripChanOrPinName = ("vfatCH","VFAT Channel")
    elif args.PanPin:
        stripChanOrPinName = ("PanPin","Panasonic Pin")
        stripChanOrPinType = mappingNames[1]
    else:
        outF.Close()
        inFile.Close()
        raise RuntimeError("anaUltraScurve(): I did not understand this (channels, PanPin) combination: ({0},{1})".format(args.channels,args.PanPin))

    # Initialize distributions
    for vfat in range(nVFATS):
        try:
            chipID = dict_chipID[vfat]
        except KeyError as err:
            chipID = 0
            if args.debug:
                printYellow("No CHIP_ID for VFAT{0}, If you don't expect data from this VFAT there's no problem".format(vfat))

        if isVFAT3:
            yMin_Charge = calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat]
            yMax_Charge = calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat]
        else:
            yMin_Charge = calDAC2Q_Slope[vfat]*-0.5+calDAC2Q_Intercept[vfat]
            yMax_Charge = calDAC2Q_Slope[vfat]*255.5+calDAC2Q_Intercept[vfat]
            pass
        if not args.PanPin:
            vSummaryPlots[vfat] = r.TH2D('vSummaryPlots{0}'.format(vfat),
                    'VFAT {0}: chipID {1};{2};{3} #left(fC#right)'.format(vfat,chipID,stripChanOrPinName[1],dacName),
                    maxChans, -0.5, maxChans-0.5,
                    256, yMin_Charge, yMax_Charge)
            vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoMaskedChan[vfat] = r.TH2D('vSummaryPlotsNoMaskedChan{0}'.format(vfat),
                    'VFAT {0}: chipID {1};{2};{3} #left(fC#right)'.format(vfat,chipID,stripChanOrPinName[1],dacName),
                    maxChans, -0.5, maxChans-0.5,
                    256, yMin_Charge, yMax_Charge)
            vSummaryPlotsNoMaskedChan[vfat].GetYaxis().SetTitleOffset(1.5)
        else:
            vSummaryPlots[vfat] = r.TH2D('vSummaryPlots{0}'.format(vfat),
                    'VFAT{0} chipID {1} Pins [0-63];63 - Panasonic Pin;{2} #left(fC#right)'.format(vfat,chipID,dacName),
                    maxChans/2, -0.5, maxChans/2-0.5,
                    256, yMin_Charge, yMax_Charge)
            vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoMaskedChan[vfat] = r.TH2D('vSummaryPlotsNoMaskedChan{0}'.format(vfat),
                    'VFAT{0} chipID {1} Pins [0-63];63 - Panasonic Pin;{2} #left(fC#right)'.format(vfat,chipID,dacName),
                    maxChans/2, -0.5, maxChans/2-0.5,
                    256, yMin_Charge, yMax_Charge)
            vSummaryPlotsNoMaskedChan[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsPanPin2[vfat] = r.TH2D('vSummaryPlotsPanPin2_{0}'.format(vfat),
                    'VFAT{0} chipID {1} Pins [64-127];127 - Panasonic Pin;{2} #left(fC#right)'.format(vfat,chipID,dacName),
                    maxChans/2, -0.5, maxChans/2-0.5,
                    256, yMin_Charge, yMax_Charge)
            vSummaryPlotsPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
            vSummaryPlotsNoMaskedChanPanPin2[vfat] = r.TH2D('vSummaryPlotsNoMaskedChanPanPin2_{0}'.format(vfat),
                    'VFAT{0} chipID {1} Pins [64-127];127 - Panasonic Pin;{2} #left(fC#right)'.format(vfat,chipID,dacName),
                    maxChans/2, -0.5, maxChans/2-0.5,
                    256, yMin_Charge, yMax_Charge)
            vSummaryPlotsNoMaskedChanPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
            pass
        for chan in range (0,maxChans):
            vthr_list[vfat].append(0)
            trim_list[vfat].append(0)
            if isVFAT3:
                trimPolarity_list[vfat].append(0)
            else:
                trimRange_list[vfat].append(0)
            pass
        pass
    
    # Build the channel to strip mapping from the text file
    import pkg_resources
    MAPPING_PATH = pkg_resources.resource_filename('gempython.gemplotting', 'mapping/')

    dict_vfatChanLUT = ndict()
    from gempython.gemplotting.utils.anautilities import getMapping
    if args.extChanMapping is not None:
        dict_vfatChanLUT = getMapping(args.extChanMapping, gemType=gemType)
    elif GEBtype == 'long':
        dict_vfatChanLUT = getMapping(MAPPING_PATH+'/longChannelMap.txt', gemType=gemType)
    elif GEBtype == 'short':
        dict_vfatChanLUT = getMapping(MAPPING_PATH+'/shortChannelMap.txt', gemType=gemType)
    else:
        outF.Close()
        inFile.Close()
        raise RuntimeError("No external mapping provided and GEB type was not recognized")
  
    # Create the fitter
    from gempython.gemplotting.fitting.fitScanData import ScanDataFitter
    if performFit:
        fitter = ScanDataFitter(
                calDAC2Q_m=calDAC2Q_Slope, 
                calDAC2Q_b=calDAC2Q_Intercept,
                isVFAT3=isVFAT3,
                nVFats = nVFATS
                )
        pass

    # Get some of the operational settings of the ASIC
    # Refactor this using root_numpy???
    dict_vfatID = dict((vfat, 0) for vfat in range(nVFATS))
    listOfBranches = scurveTree.GetListOfBranches()
    nPulses = -1
    for event in scurveTree:
        # If provided, skip all VFATs but the requested one
        if ((vfatList is not None) and (event.vfatN not in vfatList)):
            continue

        if "vthr" in listOfBranches: #v3 electronics behavior
            vthr_list[event.vfatN][event.vfatCH] = event.vthr
        else: #v2b electronics behavior
            vthr_list[event.vfatN][event.vfatCH] = abs(event.vth2 - event.vth1)
            pass
        trim_list[event.vfatN][event.vfatCH] = event.trimDAC
        if isVFAT3:
            trimPolarity_list[event.vfatN][event.vfatCH] = event.trimPolarity
        else:
            trimRange_list[event.vfatN][event.vfatCH] = event.trimRange
        
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
        if performFit:
            fitter.feed(event)

    # Loop over input data and fill histograms
    print("Filling Histograms")
    fill2DScurveSummaryPlots(
            scurveTree=scurveTree, 
            vfatHistos=vSummaryPlots, 
            vfatChanLUT=dict_vfatChanLUT, 
            vfatHistosPanPin2=vSummaryPlotsPanPin2, 
            lutType=stripChanOrPinType, 
            chanMasks=None, 
            calDAC2Q_m=calDAC2Q_Slope, 
            calDAC2Q_b=calDAC2Q_Intercept,
            vfatList=vfatList,
            gemType=gemType
    )
    
    if performFit:
        # Fit Scurves        
        print("Fitting Histograms")
        fitSummary = open(outputDir+'/fitSummary.txt','w')
        fitSummary.write('vfatN/I:vfatID/I:vfatCH/I:fitP0/F:fitP1/F:fitP2/F:fitP3/F\n')
        scanFitResults = fitter.fit(debug=args.debug)
        for vfat in range(nVFATS):
            # If provided, skip all VFATs but the requested one
            if ((vfatList is not None) and (vfat not in vfatList)):
                continue

            for chan in range(0,maxChans):
                fitSummary.write(
                        '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(
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
        masks = {}
        reason4Mask = {}
        effectivePedestals = [ np.zeros(maxChans) for vfat in range(nVFATS) ]
        print("| vfatN | Dead Chan | Hot Chan | Failed Fits | High Noise | High Eff Ped |")
        print("| :---: | :-------: | :------: | :---------: | :--------: | :----------: |")
        for vfat in range(nVFATS):
            # If provided, skip all VFATs but the requested one
            if ((vfatList is not None) and (vfat not in vfatList)):
                continue

            #trimValue = np.zeros(128)
            scurveMean = np.zeros(maxChans)
            channelNoise = np.zeros(maxChans)
            fitFailed = np.zeros(maxChans, dtype=bool)
            for chan in range(0, maxChans):
                # Compute values for cuts
                channelNoise[chan] = scanFitResults[1][vfat][chan]
                effectivePedestals[vfat][chan] = fitter.scanFuncs[vfat][chan].Eval(0.0)
                
                # Compute the value to apply MAD on for each channel
                #trimValue[chan] = scanFitResults[0][vfat][chan] - args.ztrim * scanFitResults[1][vfat][chan]
                scurveMean[chan] = scanFitResults[0][vfat][chan] 
                pass
            fitFailed = np.logical_not(fitter.fitValid[vfat])
            
            # Determine outliers
            from gempython.gemplotting.utils.anautilities import isOutlierMADOneSided
            #hot = isOutlierMADOneSided(trimValue, thresh=args.zscore,
            #                           rejectHighTail=False)
            hot = isOutlierMADOneSided(scurveMean, thresh=args.zscore,
                                       rejectHighTail=False) # rejects scurves with means shifted to low charge values
            
            # Create reason array
            reason = np.zeros(maxChans, dtype=int) # Not masked
            from gempython.gemplotting.utils.anaInfo import MaskReason
            reason[hot] |= MaskReason.HotChannel
            reason[fitFailed] |= MaskReason.FitFailed
            nDeadChan = 0
            for chan in range(0,len(channelNoise)):
                if (args.deadChanCutLow < channelNoise[chan] and channelNoise[chan] < args.deadChanCutHigh):
                    reason[chan] |= MaskReason.DeadChannel
                    nDeadChan+=1
                    pass
                pass
            reason[channelNoise > args.highNoiseCut ] |= MaskReason.HighNoise
            nHighEffPed = 0
            for chan in range(0, len(effectivePedestals)):
                if chan not in fitter.Nev[vfat].keys():
                    continue
                if (effectivePedestals[vfat][chan] > (args.maxEffPedPercent * fitter.Nev[vfat][chan]) ):
                    reason[chan] |= MaskReason.HighEffPed
                    nHighEffPed+=1
                    pass
                pass
            reason4Mask[vfat] = reason
            masks[vfat] = ((reason != MaskReason.NotMasked) * (reason != MaskReason.DeadChannel))
            print('| {0:5d} | {1:9d} | {2:8d} | {3:11d} | {4:10d} | {5:12d} |'.format(
                    vfat,
                    nDeadChan,
                    np.count_nonzero(hot),
                    np.count_nonzero(fitFailed),
                    np.count_nonzero(channelNoise > args.highNoiseCut),
                    nHighEffPed))
            pass
        
        # Make Distributions w/o Hot Channels
        print("Removing Hot Channels from Output Histograms")
        fill2DScurveSummaryPlots(
                scurveTree=scurveTree, 
                vfatHistos=vSummaryPlotsNoMaskedChan, 
                vfatChanLUT=dict_vfatChanLUT, 
                vfatHistosPanPin2=vSummaryPlotsNoMaskedChanPanPin2, 
                lutType=stripChanOrPinType, 
                chanMasks=masks, 
                calDAC2Q_m=calDAC2Q_Slope, 
                calDAC2Q_b=calDAC2Q_Intercept,
                vfatList=vfatList,
                gemType=gemType
        )
        
        # Set the branches of the TTree and store the results
        # Due to weird ROOT black magic this cannot be done here
        #scurveFitTree = r.TTree('scurveFitTree','Tree Holding FitData')

        from array import array
        if 'detName' in listOfBranches:
            detName = r.vector('string')()
            detName.push_back(rp.tree2array(scurveTree, branches = [ 'detName' ] )[0][0][0])
            scurveFitTree.Branch( 'detName', detName)
        chi2 = array( 'f', [ 0 ] )
        scurveFitTree.Branch( 'chi2', chi2, 'chi2/F')
        mask = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'mask', mask, 'mask/I' )
        maskReason = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'maskReason', maskReason, 'maskReason/I' )
        ndf = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'ndf', ndf, 'ndf/I')
        Nhigh = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'Nhigh', Nhigh, 'Nhigh/I')
        noise = array( 'f', [ 0 ] )
        scurveFitTree.Branch( 'noise', noise, 'noise/F')
        panPin = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'panPin', panPin, 'panPin/I' )
        pedestal = array( 'f', [ 0 ] )
        scurveFitTree.Branch( 'pedestal', pedestal, 'pedestal/F')
        ped_eff = array( 'f', [ 0 ] )
        scurveFitTree.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
        ROBstr = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'ROBstr', ROBstr, 'ROBstr/I' )
        trimDAC = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
        threshold = array( 'f', [ 0 ] )
        scurveFitTree.Branch( 'threshold', threshold, 'threshold/F')
        if isVFAT3:
            trimPolarity = array( 'i', [ 0 ] )
            scurveFitTree.Branch('trimPolarity', trimPolarity, 'trimPolarity/I' )
        else:
            trimRange = array( 'i', [ 0 ] )
            scurveFitTree.Branch( 'trimRange', trimRange, 'trimRange/I' )
        vfatCH = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
        vfatID = array( 'L', [0] )
        scurveFitTree.Branch( 'vfatID', vfatID, 'vfatID/i' ) #Hex Chip ID of VFAT
        vfatN = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'vfatN', vfatN, 'vfatN/I' )
        vthr = array( 'i', [ 0 ] )
        scurveFitTree.Branch( 'vthr', vthr, 'vthr/I' )
        scurve_h = r.TH1F()
        scurveFitTree.Branch( 'scurve_h', scurve_h)
        scurve_fit = r.TF1()
        scurveFitTree.Branch( 'scurve_fit', scurve_fit)
        #ztrim = array( 'f', [ 0 ] )
        #ztrim[0] = args.ztrim
        #scurveFitTree.Branch( 'ztrim', ztrim, 'ztrim/F')
        
        # Make output plots
        print("Storing Output Data")
        from gempython.gemplotting.mapping.chamberInfo import chamber_iEta2VFATPos, chamber_maxiEtaiPhiPair, chamber_vfatPos2iEta
        maxiEta = chamber_maxiEtaiPhiPair[gemType][0]
        maxiPhi = chamber_maxiEtaiPhiPair[gemType][1]
        
        encSummaryPlots = {}
        encSummaryPlotsByiEta = {}
        fitSummaryPlots = {}
        effPedSummaryPlots = {}
        effPedSummaryPlotsByiEta = {}
        threshSummaryPlots = {}
        threshSummaryPlotsByiEta = {}
        allENC = np.zeros(nVFATS*maxChans)
        h2DetThresh_All = r.TH2F("ScurveMean_All","ScurveMean_All",nVFATS,-0.5,nVFATS-0.5,
                                 601,-0.05,60.05)
        h2DetENC_All = r.TH2F("ScurveSigma_All","ScurveSigma_All",nVFATS,-0.5,nVFATS-0.5,
                              51,-0.05,5.05)
        h2DetEffPed_All = r.TH2F("ScurveEffPed_All","Effective Pedestal All",nVFATS,-0.5,nVFATS-0.5,
                                 nPulses+1, -0.5, nPulses+0.5)

        allENCByiEta    = dict( (ieta,np.zeros(maxiPhi*maxChans)) for ieta in range(1,maxiEta+1) )
        allEffPedByiEta = dict( (ieta,(-1.*np.ones(maxiPhi*maxChans))) for ieta in range(1,maxiEta+1) )
        allThreshByiEta = dict( (ieta,np.zeros(maxiPhi*maxChans)) for ieta in range(1,maxiEta+1) )
        ## Only in python 2.7 and up
        # allENCByiEta    = { ieta:np.zeros(3*128) for ieta in range(1,9) }
        # allEffPedByiEta = { ieta:(-1.*np.ones(3*128)) for ieta in range(1,9) }
        # allThreshByiEta = { ieta:np.zeros(3*128) for ieta in range(1,9) }

        allEffPed = -1.*np.ones(nVFATS * maxChans)
        allThresh = np.zeros(nVFATS * maxChans)
        
        
        for vfat in range(nVFATS):
            # If provided, skip all VFATs but the requested one
            if ((vfatList is not None) and (vfat not in vfatList)):
                continue

            stripPinOrChanArray = np.zeros(maxChans)
            for chan in range (0, maxChans):
                # Store stripChanOrPinType to use as x-axis of fit summary plots
                stripPinOrChan = dict_vfatChanLUT[vfat][stripChanOrPinType][chan]
                
                # Determine ieta
                ieta = chamber_vfatPos2iEta[gemType][vfat]
                iphi = chamber_iEta2VFATPos[gemType][ieta][vfat]

                # Store Values for making fit summary plots
                allENC[vfat*maxChans + chan] =  scanFitResults[1][vfat][chan]
                allEffPed[vfat*maxChans + chan] = effectivePedestals[vfat][chan]
                allThresh[vfat*maxChans + chan] = scanFitResults[0][vfat][chan]
                stripPinOrChanArray[chan] = float(stripPinOrChan)
                
                allENCByiEta[ieta][(iphi-1)*chan + chan] = scanFitResults[1][vfat][chan]
                allEffPedByiEta[ieta][(iphi-1)*chan + chan] = effectivePedestals[vfat][chan]
                allThreshByiEta[ieta][(iphi-1)*chan + chan] = scanFitResults[0][vfat][chan]

                # Set arrays linked to TBranches
                chi2[0] = scanFitResults[3][vfat][chan]
                mask[0] = masks[vfat][chan]
                maskReason[0] = reason4Mask[vfat][chan]
                ndf[0] = int(scanFitResults[5][vfat][chan])
                Nhigh[0] = int(scanFitResults[4][vfat][chan])
                noise[0] = scanFitResults[1][vfat][chan]
                panPin[0] = dict_vfatChanLUT[vfat]["PanPin"][chan]
                if chan in fitter.Nev[vfat].keys():
                    ped_eff[0] = effectivePedestals[vfat][chan]/fitter.Nev[vfat][chan]
                pedestal[0] = scanFitResults[2][vfat][chan]
                ROBstr[0] = dict_vfatChanLUT[vfat]["Strip"][chan]
                threshold[0] = scanFitResults[0][vfat][chan]
                trimDAC[0] = trim_list[vfat][chan]
                if isVFAT3:
                    trimPolarity[0] = trimPolarity_list[vfat][chan]
                else:
                    trimRange[0] = trimRange_list[vfat][chan]
                vfatCH[0] = chan
                vfatID[0] = dict_vfatID[vfat]
                vfatN[0] = vfat
                vthr[0] = vthr_list[vfat][chan]
                
                # Set TObjects linked to TBranches
                holder_curve = fitter.scanHistos[vfat][chan]
                holder_curve.Copy(scurve_h)
                holder_fit = fitter.getFunc(vfat,chan).Clone('scurveFit_vfat{0}_chan{1}'.format(vfat,chan))
                holder_fit.Copy(scurve_fit)
                
                # Filling the arrays for plotting later
                if args.drawbad:
                    if (chi2[0] > 1000.0 or chi2[0] < 1.0):
                        canvas = r.TCanvas('canvas', 'canvas', 500, 500)
                        r.gStyle.SetOptStat(1111111)
                        scurve_h.Draw()
                        scurve_fit.Draw('SAME')
                        canvas.Update()
                        canvas.SaveAs('Fit_Overlay_vfat{0}_vfatCH{1}.png'.format(VFAT, chan))
                        pass
                    pass
                scurveFitTree.Fill()
                pass

            # Make fit Summary plot
            fitSummaryPlots[vfat] = r.TGraphErrors(
                    maxChans,
                    stripPinOrChanArray,
                    allThresh[(vfat*maxChans):((vfat+1)*maxChans)],
                    np.zeros(maxChans),
                    allENC[(vfat*maxChans):((vfat+1)*maxChans)]
                    )
            fitSummaryPlots[vfat].SetTitle("VFAT {0} Fit Summary;Channel;Threshold #left(fC#right)".format(vfat))
            
            if not (args.channels or args.PanPin):
                fitSummaryPlots[vfat].GetXaxis().SetTitle("Strip")
                pass
            elif args.PanPin:
                fitSummaryPlots[vfat].GetXaxis().SetTitle("Panasonic Pin")
                pass
            
            fitSummaryPlots[vfat].SetName("gFitSummary_VFAT{0}".format(vfat))
            fitSummaryPlots[vfat].SetMarkerStyle(2)
            
            # Make thresh summary plot - bin size is variable
            thisVFAT_ThreshMean = np.mean(allThresh[(vfat*maxChans):((vfat+1)*maxChans)])
            thisVFAT_ThreshStd = np.std(allThresh[(vfat*maxChans):((vfat+1)*maxChans)])
            histThresh = r.TH1F("scurveMean_vfat{0}".format(vfat),
                                "VFAT {0};S-Curve Mean #left(fC#right);N".format(vfat),
                                40, thisVFAT_ThreshMean - 5. * thisVFAT_ThreshStd, thisVFAT_ThreshMean + 5. * thisVFAT_ThreshStd )
            histThresh.Sumw2()
            if thisVFAT_ThreshStd != 0: # Don't fill if we still at initial values
                for thresh in allThresh[(vfat*maxChans):((vfat+1)*maxChans)]:
                    if thresh == 0: # Skip the case where it still equals the inital value
                        continue
                    histThresh.Fill(thresh)
                    h2DetThresh_All.Fill(vfat,thresh)
                    pass
                pass
            gThresh = r.TGraphErrors(histThresh)
            gThresh.SetName("gScurveMeanDist_vfat{0}".format(vfat))
            gThresh.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
            gThresh.GetYaxis().SetTitle("Entries / {0} fC".format(thisVFAT_ThreshStd/4.))
            threshSummaryPlots[vfat] = gThresh

            # Make effective pedestal summary plot - bin size is fixed
            histEffPed = r.TH1F("scurveEffPed_vfat{0}".format(vfat),"VFAT {0};S-Curve Effective Pedestal #left(N#right);N".format(vfat),
                                nPulses+1, -0.5, nPulses+0.5)
            histEffPed.Sumw2()
            for effPed in allEffPed[(vfat*maxChans):((vfat+1)*maxChans)]:
                if effPed < 0: # Skip the case where it still equals the inital value
                    continue
                histEffPed.Fill(effPed)
                h2DetEffPed_All.Fill(vfat,effPed)
                pass
            pass
            histEffPed.SetMarkerStyle(21)
            histEffPed.SetMarkerColor(r.kRed)
            histEffPed.SetLineColor(r.kRed)
            effPedSummaryPlots[vfat] = histEffPed
            
            # Make enc summary plot bin size is variable
            thisVFAT_ENCMean = np.mean(allENC[(vfat*maxChans):((vfat+1)*maxChans)])
            thisVFAT_ENCStd = np.std(allENC[(vfat*maxChans):((vfat+1)*maxChans)])
            histENC = r.TH1F("scurveSigma_vfat{0}".format(vfat),"VFAT {0};S-Curve Sigma #left(fC#right);N".format(vfat),
                                40, thisVFAT_ENCMean - 5. * thisVFAT_ENCStd, thisVFAT_ENCMean + 5. * thisVFAT_ENCStd )
            histENC.Sumw2()
            if thisVFAT_ENCStd != 0: # Don't fill if we are still at initial values
                for enc in allENC[(vfat*maxChans):((vfat+1)*maxChans)]:
                    if enc == 0: # Skip the case where it still equals the inital value
                        continue
                    histENC.Fill(enc)
                    h2DetENC_All.Fill(vfat,enc)
                    pass
                pass
            gENC = r.TGraphErrors(histENC)
            gENC.SetName("gScurveSigmaDist_vfat{0}".format(vfat))
            gENC.GetXaxis().SetTitle("scurve sigma #left(fC#right)")
            gENC.GetYaxis().SetTitle("Entries / {0} fC".format(thisVFAT_ENCStd/4.))
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
        hDetThresh_All.GetYaxis().SetTitle("Entries / {0} fC".format(detThresh_Std/10.))
        gDetThresh_All = r.TGraphErrors(hDetThresh_All)
        gDetThresh_All.SetName("gScurveMeanDist_All")
        gDetThresh_All.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
        gDetThresh_All.GetYaxis().SetTitle("Entries / {0} fC".format(detThresh_Std/10.))

        # Make a thresh map dist for the entire detector
        from gempython.gemplotting.utils.anautilities import get2DMapOfDetector
        hDetMapThresh = get2DMapOfDetector(dict_vfatChanLUT, allThresh, stripChanOrPinType, "threshold", gemType=gemType)
        hDetMapThresh.SetZTitle("threshold #left(fC#right)")

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

        h2DetEffPed_All.GetXaxis().SetTitle("VFAT Position")
        h2DetEffPed_All.GetYaxis().SetTitle("Effective Pedestal")

        # Make a EffPed map dist for the entire detector
        hDetMapEffPed = get2DMapOfDetector(dict_vfatChanLUT, allEffPed, stripChanOrPinType, "Effective Pedestal", gemType=gemType)
        hDetMapEffPed.SetZTitle("Effective Pedestal")

        # Make a ENC Summary Dist For the entire Detector
        detENC_Mean = np.mean(allENC[allENC != 0]) #Don't consider intial values
        detENC_Std = np.std(allENC[allENC != 0]) #Don't consider intial values
        hDetENC_All = r.TH1F("hScurveSigmaDist_All","All VFATs;S-Curve Sigma #left(fC#right);N",
                            100, detENC_Mean - 5. * detENC_Std, detENC_Mean + 5. * detENC_Std )
        for enc in allENC[allENC != 0]:
            hDetENC_All.Fill(enc)
            pass
        hDetENC_All.GetXaxis().SetTitle("scurve sigma #left(fC#right)")
        hDetENC_All.GetYaxis().SetTitle("Entries / {0} fC".format(detENC_Std/10.))
        gDetENC_All = r.TGraphErrors(hDetENC_All)
        gDetENC_All.SetName("gScurveSigmaDist_All")
        gDetENC_All.GetXaxis().SetTitle("scurve sigma #left(fC#right)")
        gDetENC_All.GetYaxis().SetTitle("Entries / {0} fC".format(detENC_Std/10.))
        
        # Make a ENC map dist for the entire detector
        hDetMapENC = get2DMapOfDetector(dict_vfatChanLUT, allENC, stripChanOrPinType, "noise", gemType=gemType)
        hDetMapENC.SetZTitle("noise #left(fC#right)")
        #hDetMapENC.GetZaxis().SetRangeUser(0.5,0.30)

        # Make the plots by iEta
        for ieta in range(1,maxiEta+1):
            # S-curve mean position (threshold)
            ietaThresh_Mean = np.mean(allThreshByiEta[ieta][allThreshByiEta[ieta] != 0])
            ietaThresh_Std = np.std(allThreshByiEta[ieta][allThreshByiEta[ieta] != 0])

            hThresh_iEta = r.TH1F(
                    "hScurveMeanDist_ieta{0}".format(ieta),
                    "i#eta={0};S-Curve Mean #left(fC#right);N".format(ieta),
                    80, 
                    ietaThresh_Mean - 5. * ietaThresh_Std, 
                    ietaThresh_Mean + 5. * ietaThresh_Std )
            
            for thresh in allThreshByiEta[ieta][allThreshByiEta[ieta] != 0]:
                hThresh_iEta.Fill(thresh)
                pass
            gThresh_iEta = r.TGraphErrors(hThresh_iEta)
            gThresh_iEta.SetName("gScurveMeanDist_ieta{0}".format(ieta))
            gThresh_iEta.GetXaxis().SetTitle("scurve mean pos #left(fC#right)")
            gThresh_iEta.GetYaxis().SetTitle("Entries / {0} fC".format(ietaThresh_Std/8.))
            threshSummaryPlotsByiEta[ieta] = gThresh_iEta

            # S-curve effective pedestal
            hEffPed_iEta = r.TH1F(
                    "hScurveEffPedDist_ieta{0}".format(ieta),
                    "i#eta={0};S-Curve Effective Pedestal #left(N#right);N".format(ieta),
                     nPulses+1, -0.5, nPulses+0.5)
            
            for effPed in allEffPedByiEta[ieta][allEffPedByiEta[ieta] > -1]:
                hEffPed_iEta.Fill(effPed)
                pass
            hEffPed_iEta.SetMarkerStyle(21)
            hEffPed_iEta.SetMarkerColor(r.kRed)
            hEffPed_iEta.SetLineColor(r.kRed)
            effPedSummaryPlotsByiEta[ieta] = hEffPed_iEta

            # S-curve sigma (enc)
            ietaENC_Mean = np.mean(allENCByiEta[ieta][allENCByiEta[ieta] != 0])
            ietaENC_Std = np.std(allENCByiEta[ieta][allENCByiEta[ieta] != 0])

            hENC_iEta = r.TH1F(
                    "hScurveSigmaDist_ieta{0}".format(ieta),
                    "i#eta={0};S-Curve Sigma #left(fC#right);N".format(ieta),
                    80, 
                    ietaENC_Mean - 5. * ietaENC_Std, 
                    ietaENC_Mean + 5. * ietaENC_Std )
            
            for enc in allENCByiEta[ieta][allENCByiEta[ieta] != 0]:
                hENC_iEta.Fill(enc)
                pass
            gENC_iEta = r.TGraphErrors(hENC_iEta)
            gENC_iEta.SetName("gScurveSigmaDist_ieta{0}".format(ieta))
            gENC_iEta.GetXaxis().SetTitle("scurve sigma pos #left(fC#right)")
            gENC_iEta.GetYaxis().SetTitle("Entries / {0} fC".format(ietaENC_Std/8.))
            encSummaryPlotsByiEta[ieta] = gENC_iEta
            pass
        pass # end if performFit

    # Save the summary plots and channel config file
    from gempython.gemplotting.utils.anautilities import getSummaryCanvas, getSummaryCanvasByiEta
    if args.PanPin:
        getSummaryCanvas(vSummaryPlots, vSummaryPlotsPanPin2, '{0}/Summary.png'.format(outputDir), gemType=gemType, write2Disk=True) 
    else: 
        getSummaryCanvas(vSummaryPlots, None, '{0}/Summary.png'.format(outputDir), gemType=gemType, write2Disk=True)

    if performFit:
        if args.PanPin:
            getSummaryCanvas(vSummaryPlotsNoMaskedChan, vSummaryPlotsNoMaskedChanPanPin2, '{0}/PrunedSummary.png'.format(outputDir), gemType=gemType, write2Disk=True)
        else:
            getSummaryCanvas(vSummaryPlotsNoMaskedChan, None, '{0}/PrunedSummary.png'.format(outputDir), gemType=gemType, write2Disk=True)
        getSummaryCanvas(fitSummaryPlots, None, '{0}/fitSummary.png'.format(outputDir), None, drawOpt="APE1", gemType=gemType, write2Disk=True)
        getSummaryCanvas(threshSummaryPlots, None, '{0}/ScurveMeanSummary.png'.format(outputDir), None, drawOpt="AP", gemType=gemType, write2Disk=True)
        getSummaryCanvas(effPedSummaryPlots, None, '{0}/ScurveEffPedSummary.png'.format(outputDir), None, drawOpt="E1", gemType=gemType, write2Disk=True)
        getSummaryCanvas(encSummaryPlots, None, '{0}/ScurveSigmaSummary.png'.format(outputDir), None, drawOpt="AP", gemType=gemType, write2Disk=True)
        
        #BoxPlot
        try:
            minThreshRange = np.nanmin(allThresh[allThresh != 0])*0.9
        except ValueError:
            minThreshRange = 0
            pass
        try:
            maxThreshRange = np.nanmax(allThresh[allThresh != 0])*1.1
        except ValueError:
            maxThreshRange = 80
            pass
        canvasBoxPlot_Thresh = r.TCanvas("h2Thresh","h2Thresh",0,0,1200,1000)
        h2DetThresh_All.SetStats(0)
        h2DetThresh_All.GetXaxis().SetTitle("VFAT position")
        h2DetThresh_All.GetYaxis().SetRangeUser(minThreshRange,maxThreshRange)
        h2DetThresh_All.GetYaxis().SetTitle("Threshold #left(fC#right)")
        h2DetThresh_All.SetFillColor(400)
        h2DetThresh_All.Draw("candle1")
        canvasBoxPlot_Thresh.Update()
        canvasBoxPlot_Thresh.SaveAs("{0}/h2ScurveMeanDist_All.png".format(outputDir))
        canvasBoxPlot_Thresh.Close()

        canvasBoxPlot_EffPed = r.TCanvas("h2EffPed","h2EffPed",0,0,1200,1000)
        h2DetEffPed_All.SetStats(0)
        h2DetEffPed_All.GetXaxis().SetTitle("VFAT position")
        h2DetEffPed_All.GetYaxis().SetRangeUser(0, nevts*0.1)
        h2DetEffPed_All.GetYaxis().SetTitle("Effective Pedestal #left(A.U.#right)")
        h2DetEffPed_All.SetFillColor(400)
        h2DetEffPed_All.Draw("candle1")
        canvasBoxPlot_EffPed.Update()
        canvasBoxPlot_EffPed.SaveAs("{0}/h2ScurveEffPedDist_All.png".format(outputDir))
        canvasBoxPlot_EffPed.Close()
        
        canvasBoxPlot_ENC = r.TCanvas("h2ENC","h2ENC",0,0,1200,1000)
        h2DetENC_All.SetStats(0)
        h2DetENC_All.GetXaxis().SetTitle("VFAT position")
        h2DetENC_All.GetYaxis().SetTitle("Noise #left(fC#right)")
        h2DetENC_All.SetFillColor(400)
        h2DetENC_All.Draw("candle1")
        canvasBoxPlot_ENC.Update()
        canvasBoxPlot_ENC.SaveAs("{0}/h2ScurveSigmaDist_All.png".format(outputDir))
        canvasBoxPlot_ENC.Close()


        
        getSummaryCanvasByiEta(threshSummaryPlotsByiEta, name='{0}/ScurveMeanSummaryByiEta.png'.format(outputDir), drawOpt="AP", gemType=gemType, write2Disk=True)
        getSummaryCanvasByiEta(effPedSummaryPlotsByiEta, name='{0}/ScurveEffPedSummaryByiEta.png'.format(outputDir), drawOpt="E1", gemType=gemType, write2Disk=True)
        getSummaryCanvasByiEta(encSummaryPlotsByiEta, name='{0}/ScurveSigmaSummaryByiEta.png'.format(outputDir), drawOpt="AP", gemType=gemType, write2Disk=True)

        confF = open(outputDir+'/chConfig.txt','w')
        if isVFAT3:
            confF.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I:maskReason/I\n')
            for vfat in range(nVFATS):
                # If provided, skip all VFATs but the requested one
                if ((vfatList is not None) and (vfat not in vfatList)):
                    continue

                for chan in range(0, maxChans):
                    confF.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(
                        vfat,
                        dict_vfatID[vfat],
                        chan,
                        trim_list[vfat][chan],
                        trimPolarity_list[vfat][chan],
                        masks[vfat][chan],
                        reason4Mask[vfat][chan]))
        else:
            confF.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:mask/I:maskReason/I\n')
            for vfat in range(nVFATS):
                # If provided, skip all VFATs but the requested one
                if ((vfatList is not None) and (vfat not in vfatList)):
                    continue

                for chan in range (0, maxChans):
                    confF.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(
                        vfat,
                        dict_vfatID[vfat],
                        chan,
                        trim_list[vfat][chan],
                        masks[vfat][chan],
                        reason4Mask[vfat][chan]))
        confF.close()

    # Make 1D Plot for each VFAT showing all scurves
    # Don't use the ones stored in fitter since this may not exist (e.g. performFit = false)
    canvOfScurveHistosNoMaskedChan = {}
    if args.PanPin:
        canvOfScurveHistos = plotAllSCurvesOnCanvas(vSummaryPlots,vSummaryPlotsPanPin2,"scurves")
    else:
        canvOfScurveHistos = plotAllSCurvesOnCanvas(vSummaryPlots,None,"scurves")

    if performFit:
        if args.PanPin:
            canvOfScurveHistosNoMaskedChan = plotAllSCurvesOnCanvas(vSummaryPlotsNoMaskedChan,vSummaryPlotsNoMaskedChanPanPin2,"scurvesNoMaskedChan")
        else:
            canvOfScurveHistosNoMaskedChan = plotAllSCurvesOnCanvas(vSummaryPlotsNoMaskedChan,None,"scurvesNoMaskedChan")
        
        canvOfScurveFits = {}
        for vfat in range(nVFATS):
            # If provided, skip all VFATs but the requested one
            if ((vfatList is not None) and (vfat not in vfatList)):
                continue

            canvOfScurveFits[vfat] = r.TCanvas("canv_scurveFits_vfat{0}".format(vfat),"Scurve Fits from VFAT{0}".format(vfat),600,600)
            canvOfScurveFits[vfat].cd()
            for chan in range (0,maxChans):
                if masks[vfat][chan]: # Do not draw fit for masked channels
                    continue

                if chan == 0:
                    fitter.scanFuncs[vfat][chan].Draw()
                else:
                    fitter.scanFuncs[vfat][chan].Draw("same")
            canvOfScurveFits[vfat].Update()
    
    # Save TObjects
    outF.cd()
    if performFit:
        scurveFitTree.Write()
    for vfat in range(nVFATS):
        # If provided, skip all VFATs but the requested one
        if ((vfatList is not None) and (vfat not in vfatList)):
            continue

        dirVFAT = outF.mkdir("VFAT{0}".format(vfat))
        dirVFAT.cd()
        vSummaryPlots[vfat].Write()
        if args.PanPin:
            vSummaryPlotsPanPin2[vfat].Write()
        canvOfScurveHistos[vfat].Write()
        if performFit:
            vSummaryPlotsNoMaskedChan[vfat].Write()
            if args.PanPin:
                vSummaryPlotsNoMaskedChanPanPin2[vfat].Write()
            fitSummaryPlots[vfat].Write()
            threshSummaryPlots[vfat].Write()
            effPedSummaryPlots[vfat].Write()
            encSummaryPlots[vfat].Write()
            canvOfScurveHistosNoMaskedChan[vfat].Write()
            canvOfScurveFits[vfat].Write()
            pass
    if performFit:
        dirSummary = outF.mkdir("Summary")
        dirSummary.cd()
        hDetThresh_All.Write()
        hDetEffPed_All.Write()
        hDetENC_All.Write()
        
        gDetThresh_All.Write()
        gDetEffPed_All.Write()
        gDetENC_All.Write()
   
        h2DetThresh_All.Write()
        h2DetEffPed_All.Write()
        h2DetENC_All.Write()

        hDetMapThresh.Write()
        hDetMapEffPed.Write()
        hDetMapENC.Write()

        for ieta in range(1,maxiEta+1):
            dir_iEta = dirSummary.mkdir("ieta{0}".format(ieta))
            dir_iEta.cd()
            threshSummaryPlotsByiEta[ieta].Write()
            effPedSummaryPlotsByiEta[ieta].Write()
            encSummaryPlotsByiEta[ieta].Write()
            pass
        pass

    if performFit:
        list_bNames = ['mask','maskReason','noise','pedestal','ped_eff','threshold','vfatCH','vfatID','vfatN']
        array_fitData = rp.tree2array(scurveFitTree,branches=list_bNames)
        
        outF.Close()
        inFile.Close()
        return array_fitData
    else:
        outF.Close()
        inFile.Close()
        return

def fill2DScurveSummaryPlots(scurveTree, vfatHistos, vfatChanLUT, vfatHistosPanPin2=None, lutType="vfatCH", chanMasks=None, calDAC2Q_m=None, calDAC2Q_b=None, vfatList=None, gemType="ge11"):
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
    vfatList - List of VFAT positions to consider in the analysis, if None analyzes all (default). Useful for debugging
    """
    from gempython.gemplotting.utils.anaInfo import dict_calSF, mappingNames
    from gempython.gemplotting.utils.anautilities import first_index_gt
    from gempython.tools.hw_constants import vfatsPerGemVariant
    from math import sqrt

    # Check if lutType is expected
    if lutType not in mappingNames:
        print("fill2DScurveSummaryPlots() - lutType '{0}' not supported".format(lutType))
        print("fill2DScurveSummaryPlots() - I was expecting one of the following: ", mappingNames)
        raise LookupError

    # Set calDAC2Q slope to unity if not provided
    if calDAC2Q_m is None:
        calDAC2Q_m = np.ones(vfatsPerGemVariant[gemType])

    # Set calDAC2Q intercept to zero if not provided
    if calDAC2Q_b is None:
        calDAC2Q_b = np.zeros(vfatsPerGemVariant[gemType])
   
    # Get list of bin edges in Y
    # Must be done for each VFAT since the conversion from DAC units to fC may be unique to the VFAT
    listOfBinEdgesY = {}
    for vfat in vfatHistos:
        listOfBinEdgesY[vfat] = [ vfatHistos[vfat].GetYaxis().GetBinLowEdge(binY) 
                for binY in range(1,vfatHistos[vfat].GetNbinsY()+2) ] #Include overflow
        pass

    # check current pulse?
    checkCurrentPulse = False
    listOfBranchNames = [branch.GetName() for branch in scurveTree.GetListOfBranches() ]
    if "isCurrentPulse" in listOfBranchNames:
        checkCurrentPulse = True
        pass

    # Fill Histograms
    for event in scurveTree:
        # If provided, skip all VFATs but the requested one
        if ((vfatList is not None) and (event.vfatN not in vfatList)):
            continue

        # Skip entry if channel is masked
        if chanMasks is not None:
            if chanMasks[event.vfatN][event.vfatCH]:
                continue

        # Get the channel, strip, or Pan Pin
        stripPinOrChan = vfatChanLUT[event.vfatN][lutType][event.vfatCH]

        # Determine charge
        charge = calDAC2Q_m[event.vfatN]*event.vcal+calDAC2Q_b[event.vfatN]
        if checkCurrentPulse: #Potentially v3 electronics
            if event.isCurrentPulse:
                #Q = CAL_DUR * CAL_DAC * 10nA * CAL_FS
                charge = (1./ 40079000) * event.vcal * (10 * 1e-9) * dict_calSF[event.calSF] * 1e15
        
        # Determine the binY that corresponds to this charge value
        chargeBin = first_index_gt(listOfBinEdgesY[event.vfatN], charge)-1

        # Fill Summary Histogram
        from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans
        if lutType is mappingNames[1] and vfatHistosPanPin2 is not None:
            if (stripPinOrChan < maxChans/2):
                vfatHistos[event.vfatN].SetBinContent(maxChans/2-stripPinOrChan,chargeBin,event.Nhits)
                vfatHistos[event.vfatN].SetBinError(maxChans/2-stripPinOrChan+1,chargeBin,sqrt(event.Nhits))
                pass
            else:
                vfatHistosPanPin2[event.vfatN].SetBinContent(maxChans-stripPinOrChan,chargeBin,event.Nhits)
                vfatHistosPanPin2[event.vfatN].SetBinError(maxChans-stripPinOrChan,chargeBin,sqrt(event.Nhits))
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
        canv_dict[vfat] = r.TCanvas("canv_{0}_vfat{1}".format(obsName,vfat),"{0} from VFAT{1}".format(obsName,vfat),600,600)
        canv_dict[vfat].Draw()
        canv_dict[vfat].cd()
        for binX in range(1,histo.GetNbinsX()+1):
            h_scurve = histo.ProjectionY("h_{0}_vfat{1}_bin{2}".format(obsName,vfat,binX),binX,binX,"")
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
                h_scurve = histo.ProjectionY("h_{0}_vfat{1}_bin{2}".format(obsName,vfat,binX),binX,binX,"")
                h_scurve.SetLineColor(r.kBlue+2)
                h_scurve.SetLineWidth(2)
                h_scurve.SetFillStyle(0)
                h_scurve.Draw("same")

                g_scurve = r.TGraph(h_scurve)
            canv_dict[vfat].Update()

    return canv_dict
