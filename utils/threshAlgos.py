r"""
``threshAlgos`` --- Utilities for analyzing threshold scan data
===============================================================

.. code-block:: python

    import gempython.gemplotting.utils.threshAlgos

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Utilities for analyzing threshold scan data

Documentation
-------------
"""

def anaUltraThresholdStar(inputs):
    """
    Wrapper to be used with multiprocessing.Pool methods
    See: https://stackoverflow.com/questions/5442910/python-multiprocessing-pool-map-for-multiple-arguments

    When moving to python 3.X we should use the Pool::starmap function and not this wrapper:
    see: https://stackoverflow.com/a/5442981
    """
    return anaUltraThreshold(*inputs)

def anaUltraThreshold(args,thrFilename,GEBtype="short",outputDir=None,fileScurveFitTree=None):
    """
    Performs the threshold analysis on the input TFile thrFilename containing the TTree thrTree.  The args namespace is expected to have the following attributes
    If this is called by a child process sys.stdout will be overwritten and be "outputDir/anaLog.log" if outputDir is not None or "$ELOG_PATH/anaLog.log" if outputDir is None.  If this is called by the MainProcess no changes to sys.stdout will be made.

    channels - If true output plots are made vs. vfatCH
    doNotSavePlots - If false saves output TObjects as a .png file to outputDir
    extChanMapping - Name of externally supplied file that specifies the ROBstr:PanPin:vfatCH mapping
    isVFAT2 - True (False) if data is coming from VFAT2(3)
    PanPin - If true output plots are made vs. PanPin
    pervfat - If true only 1D plots are made
    zscore - selection criterion to use in median absolute deviation outlier identifion algorithm

    Returns a TTree storing the analysis results if the calling process is the main process; if the
    calling process is a child process nothing is returned.

    Other arguments are:

    GEBtype - The detector type being analyzed
    thrFilename - TFile containing a TTree built from gemTreeStructure class from gempython.vfatqc.utils.treeStructure
    outputDir - Directory where output plots are stored if args.doNotSavePlots is false
    fileScurveFitTree - If this is not None it is expected to be the physical filename of a TFile containing the scurveFitTree produced by scurve analysis; the channel register data from this file will be included in the chConfig.txt produced here
    """

    # Check attributes of input args
    # If not present assign appropriate default arguments
    if hasattr(args,'channels') is False:
        args.channels = False
    if hasattr(args,'debug') is False:
        args.debug = False
    if hasattr(args,'doNotSavePlots') is False:
        args.doNotSavePlots = False
    if hasattr(args,'extChanMapping') is False:
        args.extChanMapping = None
    if hasattr(args,'isVFAT2') is False:
        args.isVFAT2 = False
    if hasattr(args,'PanPin') is False:
        args.PanPin = False
    if hasattr(args, 'pervfat') is False:
        args.pervfat = False
    if hasattr(args, 'outfilename') is False:
        args.outfilename = "ThresholdPlots.root"
    if hasattr(args,'zscore') is False:
        args.zscore = 3.5
        pass

    # Determine output filepath
    if outputDir is None:
        from gempython.gemplotting.utils.anautilities import getElogPath
        outputDir = getElogPath()
        pass

    # Redirect sys.stdout and sys.stderr if necessary
    from gempython.gemplotting.utils.multiprocUtils import redirectStdOutAndErr
    redirectStdOutAndErr("anaUltraLatency",outputDir)

    # Build the channel to strip mapping from the text file
    #from gempython.tools.hw_constants import gemVariants
    import pkg_resources
    MAPPING_PATH = pkg_resources.resource_filename('gempython.gemplotting', 'mapping/')

    from gempython.utils.nesteddict import nesteddict as ndict
    dict_vfatChanLUT = ndict()
    from gempython.gemplotting.utils.anautilities import getMapping
    if args.extChanMapping is not None:
        dict_vfatChanLUT = getMapping(extChanMapping)
    elif GEBtype == 'long':
        dict_vfatChanLUT = getMapping(MAPPING_PATH+'/longChannelMap.txt')
    elif GEBtype == 'short':
        dict_vfatChanLUT = getMapping(MAPPING_PATH+'/shortChannelMap.txt')
    else:
        raise RuntimeError("No external mapping provided and GEB type was not recognized")

    
    print('Initializing Histograms')
    if args.isVFAT2:
        dacName = "VThreshold1"
    else:
        dacName = "CFG_THR_ARM_DAC"
        pass

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
        raise RuntimeError("anaUltraThreshold(): I did not understand this (channels, PanPin) combination: ({0},{1})".format(args.channels,args.PanPin))

    # Attempt to open input TFile
    import ROOT as r
    inFile = r.TFile(thrFilename,'read')
    if not inFile.IsOpen():
        inFile.Close()
        raise IOError("Unable to open input file {0} check to make sure you have read permissions".format(thrFilename))
    if inFile.IsZombie():
        inFile.Close()
        raise IOError("Input file {0} is a Zombie, check to make sure you have write permissions and file has expected size".format(thrFilename))
    thrTree = inFile.thrTree

    import numpy as np
    import root_numpy as rp
    
    ##### FIXME
    from gempython.gemplotting.mapping.chamberInfo import gemTypeMapping
    if 'gemType' not in thrTree.GetListOfBranches():
        gemType = "ge11"
    else:
        gemType = gemTypeMapping[rp.tree2array(tree=thrTree, branches =[ 'gemType' ] )[0][0]]
    print gemType
    ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans

    
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_vfatChanLUT = ndict()
    from gempython.gemplotting.utils.anautilities import getMapping
    if args.extChanMapping is not None:
        dict_vfatChanLUT = getMapping(extChanMapping, gemType=gemType)
    elif GEBtype == 'long':
        dict_vfatChanLUT = getMapping(MAPPING_PATH+'/longChannelMap.txt', gemType=gemType)
    elif GEBtype == 'short':
        dict_vfatChanLUT = getMapping(MAPPING_PATH+'/shortChannelMap.txt', gemType=gemType)
    else:
        raise RuntimeError("No external mapping provided and GEB type was not recognized")

    listOfBranches = thrTree.GetListOfBranches()
    if 'vfatID' in listOfBranches:
        array_chipID = np.unique(rp.tree2array(thrTree, branches = [ 'vfatID','vfatN' ] ))
        dict_chipID = {}
        for entry in array_chipID:
            dict_chipID[entry['vfatN']]=entry['vfatID']
    else:
        dict_chipID = { vfat:0 for vfat in range(nVFATS) }

    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    THR_DAC_MAX = 255
    dict_h2D_thrDAC = ndict()
    dict_hMaxThrDAC = {}
    dict_hMaxThrDAC_NoOutlier = {}
    dict_chanMaxThrDAC = {}
    for vfat in range(0,nVFATS):
        if vfat not in dict_chipID:
            dict_h2D_thrDAC[vfat] = r.TH2D()
            continue
        
        chipID = dict_chipID[vfat]
        dict_h2D_thrDAC[vfat] = r.TH2D(
                'h_thrDAC_vs_ROBstr_VFAT{0}'.format(vfat),
                'VFAT{0} chipID {1};{2};{3} [DAC units]'.format(vfat,chipID,stripChanOrPinName[1],dacName),
                maxChans, -0.5, maxChans-0.5, THR_DAC_MAX+1,-0.5,THR_DAC_MAX+0.5)
        dict_hMaxThrDAC[vfat] = r.TH1F(
                'vfat{0}ChanMaxthrDAC'.format(vfat),
                "VFAT{0} chipID {1}".format(vfat,chipID),
                THR_DAC_MAX+1,-0.5,THR_DAC_MAX+0.5)
        dict_hMaxThrDAC_NoOutlier[vfat]= r.TH1F(
                'vfat{0}ChanMaxthrDAC_NoOutlier'.format(vfat),
                "VFAT{0} chipID {1}".format(vfat,chipID),
                THR_DAC_MAX+1,-0.5,THR_DAC_MAX+0.5)
        dict_hMaxThrDAC_NoOutlier[vfat].SetLineColor(r.kRed)
        pass

    print('Filling Histograms')
    if args.isVFAT2:
        dict_trimRange = dict((vfat,0) for vfat in range(0,nVFATS))
    for event in thrTree:
        if args.isVFAT2:
            dict_trimRange[int(event.vfatN)] = int(event.dict_trimRange)

        stripPinOrChan = dict_vfatChanLUT[event.vfatN][stripChanOrPinType][event.vfatCH]
        dict_h2D_thrDAC[event.vfatN].Fill(stripPinOrChan,event.vth1,event.Nhits)
        pass

    # Make output TFile and make output TTree
    from array import array
    outFile = r.TFile("{0}/{1}".format(outputDir,args.outfilename),"RECREATE")
    thrAnaTree = r.TTree('thrAnaTree','Tree Holding Analyzed Threshold Data')
    if 'detName' in listOfBranches:
        detName = r.vector('string')()
        detName.push_back(rp.tree2array(thrTree, branches = [ 'detName' ] )[0][0][0])
        thrAnaTree.Branch('detName', detName)
    mask = array( 'i', [ 0 ] )
    thrAnaTree.Branch( 'mask', mask, 'mask/I' )
    maskReason = array( 'i', [ 0 ] )
    thrAnaTree.Branch( 'maskReason', maskReason, 'maskReason/I' )
    vfatCH = array( 'i', [ 0 ] )
    vfatCH[0] = -1
    if args.isVFAT2:
        trimRange = array( 'i', [0] )
        thrAnaTree.Branch( 'trimRange', trimRange, 'trimRange/I')
    thrAnaTree.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    vfatID = array( 'L', [0] )
    thrAnaTree.Branch( 'vfatID', vfatID, 'vfatID/i' ) #Hex Chip ID of VFAT
    vfatN = array( 'i', [ 0 ] )
    thrAnaTree.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vthr = array( 'i', [ 0 ] )
    thrAnaTree.Branch( 'vthr', vthr, 'vthr/I' )

    #Determine Hot Channels
    print('Determining hot channels')

    from gempython.gemplotting.utils.anaInfo import MaskReason
    from gempython.gemplotting.utils.anautilities import isOutlierMADOneSided
    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
    hot_channels = {}
    for vfat in range(0,nVFATS):
        if vfat not in dict_chipID:
            continue
        
        #For each channel determine the maximum thresholds
        dict_chanMaxThrDAC[vfat] = -1 * np.ones((2,dict_h2D_thrDAC[vfat].GetNbinsX()))
        for chan in range(0,maxChans):
            chanProj = dict_h2D_thrDAC[vfat].ProjectionY("projY",chan+1,chan+1,"")
            for thresh in range(chanProj.GetMaximumBin(),THR_DAC_MAX+1):
                if(chanProj.GetBinContent(thresh) == 0):
                    dict_chanMaxThrDAC[vfat][0][chan]=chan
                    dict_chanMaxThrDAC[vfat][1][chan]=(thresh-1)
                    dict_hMaxThrDAC[vfat].Fill(thresh-1)
                    break
                pass
            pass

        #Determine Outliers (e.g. "hot" channels)
        hot_channels[vfat] = [ False for chan in range(0,maxChans) ]
        chanOutliers = isOutlierMADOneSided(dict_chanMaxThrDAC[vfat][1,:], thresh=args.zscore)
        for chan in range(0,len(chanOutliers)):
            hot_channels[vfat][chan] = chanOutliers[chan]

            if not chanOutliers[chan]:
                dict_hMaxThrDAC_NoOutlier[vfat].Fill(dict_chanMaxThrDAC[vfat][1][chan])
                pass
            pass

        #Fill TTree
        for chan in range(0,maxChans):
            mask[0] = hot_channels[vfat][chan]
            if hot_channels[vfat][chan]:
                maskReason[0] = MaskReason.HotChannel
            else:
                maskReason[0] = 0x0
            if args.isVFAT2:
                trimRange[0] = dict_trimRange[vfat]
            vfatCH[0] = chan
            vfatID[0] = dict_chipID[vfat]
            vfatN[0] = vfat
            vthr[0] = int(dict_chanMaxThrDAC[vfat][1][chan])
            thrAnaTree.Fill()
            pass
        pass

    #Save Output
    from gempython.gemplotting.utils.anautilities import getSummaryCanvas, addPlotToCanvas
    if not args.doNotSavePlots:
        getSummaryCanvas(dictSummary=dict_h2D_thrDAC, name='{0}/ThreshSummary.png'.format(outputDir), drawOpt="colz", gemType=gemType, write2Disk=True)

        dict_h2D_thrDACProj = {}
        for vfat in range(0, nVFATS):
            dict_h2D_thrDACProj[vfat] = dict_h2D_thrDAC[vfat].ProjectionY()
            pass
        getSummaryCanvas(dictSummary=dict_h2D_thrDACProj, name='{0}/VFATSummary.png'.format(outputDir), drawOpt="", gemType=gemType, write2Disk=True)

        #Save thrDACMax Distributions Before/After Outlier Rejection
        canv_vt1Max = getSummaryCanvas(dict_hMaxThrDAC, name="canv_vt1Max", drawOpt="hist", gemType=gemType)
        canv_vt1Max = addPlotToCanvas(canv=canv_vt1Max, content=dict_hMaxThrDAC_NoOutlier, drawOpt="hist", gemType=gemType)
        canv_vt1Max.SaveAs(outputDir+'/thrDACMaxSummary.png')
        
    # Fetch trimDAC & chMask from scurveFitTree
    import numpy as np
    import root_numpy as rp
    dict_vfatTrimMaskData = {}
    if fileScurveFitTree is not None:
        list_bNames = ["vfatN"]
        if not (args.channels or args.PanPin):
            list_bNames.append("ROBstr")
            pass
        elif args.channels:
            list_bNames.append("vfatCH")
            pass
        elif args.PanPin:
            list_bNames.append("panPin")
            pass
        list_bNames.append("mask")
        list_bNames.append("maskReason")
        list_bNames.append("trimDAC")
        if not args.isVFAT2:
            list_bNames.append("trimPolarity")

        from gempython.gemplotting.utils.anautilities import initVFATArray
        array_VFATSCurveData = rp.root2array(fileScurveFitTree,treename="scurveFitTree",branches=list_bNames)
        dict_vfatTrimMaskData = dict((idx,initVFATArray(array_VFATSCurveData.dtype)) for idx in np.unique(array_VFATSCurveData[list_bNames[0]]))
        for dataPt in array_VFATSCurveData:
            dict_vfatTrimMaskData[dataPt['vfatN']][dataPt[list_bNames[1]]]['mask'] =  dataPt['mask']
            dict_vfatTrimMaskData[dataPt['vfatN']][dataPt[list_bNames[1]]]['maskReason'] =  dataPt['maskReason']
            dict_vfatTrimMaskData[dataPt['vfatN']][dataPt[list_bNames[1]]]['trimDAC'] =  dataPt['trimDAC']
            dict_vfatTrimMaskData[dataPt['vfatN']][dataPt[list_bNames[1]]]['trimPolarity'] =  dataPt['trimPolarity']
            pass
        pass

    #Subtracting off the hot channels, so the projection shows only usable ones.
    list_bNames = ['vfatN','vfatCH','mask']
    hot_channels = rp.tree2array(thrAnaTree, branches=list_bNames)
    if not args.pervfat:
        print("Subtracting off hot channels")
        for vfat in range(0,nVFATS):
            if vfat not in dict_chipID:
                continue
            vfatChanArray = hot_channels[ hot_channels['vfatN'] == vfat ]
            for chan in range(0,dict_h2D_thrDAC[vfat].GetNbinsX()):
                isHotChan = vfatChanArray[ vfatChanArray['vfatCH'] == chan ]['mask']

                if fileScurveFitTree is not None:
                    isHotChan = (isHotChan or dict_vfatTrimMaskData[vfat][chan]['mask'])
                    pass

                if isHotChan:
                    print('VFAT {0} Strip {1} is noisy'.format(vfat,chan))
                    for thresh in range(THR_DAC_MAX+1):
                        dict_h2D_thrDAC[vfat].SetBinContent(chan, thresh, 0)
                        pass
                    pass
                pass
            pass
        pass

    outFile.cd()
    thrAnaTree.Write()
    dict_h2D_thrDACProjPruned = {}
    for vfat in range(0,nVFATS):
        #if we don't have any data for this VFAT, we just need to initialize the TH1D since it is drawn later
        if vfat not in dict_chipID:
            dict_h2D_thrDACProjPruned[vfat] = r.TH1D()
            continue                
        thisDir = outFile.mkdir("VFAT{0}".format(vfat))
        thisDir.cd()
        dict_h2D_thrDAC[vfat].Write()
        dict_hMaxThrDAC[vfat].Write()
        dict_hMaxThrDAC_NoOutlier[vfat].Write()
        dict_h2D_thrDACProjPruned[vfat] = dict_h2D_thrDAC[vfat].ProjectionY("h_thrDAC_VFAT{0}".format(vfat))
        dict_h2D_thrDACProjPruned[vfat].Write()
        pass

    #Save output plots new hot channels subtracted off
    if not args.doNotSavePlots:

        getSummaryCanvas(dictSummary=dict_h2D_thrDAC, name='{0}/ThreshPrunedSummary.png'.format(outputDir), drawOpt="colz", gemType=gemType, write2Disk=True)
        getSummaryCanvas(dictSummary=dict_h2D_thrDACProjPruned, name='{0}/VFATPrunedSummary.png'.format(outputDir), drawOpt="", gemType=gemType, write2Disk=True)

    #Now determine what thrDAC to use for configuration.  The first threshold bin with no entries for now.
    #Make a text file readable by TTree::ReadFile
    print('Determining the thrDAC values for each VFAT')
    vt1 = dict((vfat,0) for vfat in range(0,nVFATS))
    for vfat in range(0,nVFATS):
        if vfat not in dict_chipID:
            continue        
        proj = dict_h2D_thrDAC[vfat].ProjectionY()
        proj.Draw()
        for thresh in range(THR_DAC_MAX+1,0,-1):
            if (proj.GetBinContent(thresh+1)) > 10.0:
                if args.debug:
                    print('vt1 for VFAT {0} found'.format(vfat))
                vt1[vfat]=(thresh+1)
                break
            pass
        pass
    outFile.Close()

    txt_vfat = open(outputDir+"/vfatConfig.txt", 'w')
    if args.isVFAT2:
        txt_vfat.write("vfatN/I:vfatID/I:vt1/I:trimRange/I\n")
        for vfat in range(0,nVFATS):
            if vfat not in dict_chipID:
                continue
            txt_vfat.write('{0}\t{1}\t{2}\t{3}\n'.format(vfat,dict_chipID[vfat],vt1[vfat],trimRange[vfat]))
            pass
    else:
        txt_vfat.write("vfatN/I:vfatID/I:vt1/I\n")
        for vfat in range(0,nVFATS):
            if vfat not in dict_chipID:
                continue
            txt_vfat.write('{0}i\t{1}\t{2}\n'.format(vfat,dict_chipID[vfat],vt1[vfat]))
            pass
    txt_vfat.close()

    #Update channel registers configuration file
    if fileScurveFitTree is not None:
        confF = open(outputDir+'/chConfig_MasksUpdated.txt','w')
        if args.isVFAT2:
            confF.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:mask/I\n')
            if args.debug:
                print('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:mask/I\n')
            for vfat in range (0,nVFATS):
                if vfat not in dict_chipID:
                    continue                
                vfatChanArray = hot_channels[ hot_channels['vfatN'] == vfat ]
                for chan in range (0, maxChans):
                    isHotChan = vfatChanArray[ vfatChanArray['vfatCH'] == chan ]['mask']
                    if args.debug:
                        print('{0}\t{1}\t{2}\t{3}\t{4}\n'.format(
                            vfat,
                            dict_chipID[vfat],
                            chan,
                            dict_vfatTrimMaskData[vfat][chan]['trimDAC'],
                            int(isHotChan or dict_vfatTrimMaskData[vfat][chan]['mask'])))
                    confF.write('{0}\t{1}\t{2}\t{3}\t{4}\n'.format(
                        vfat,
                        dict_chipID[vfat],
                        chan,
                        dict_vfatTrimMaskData[vfat][chan]['trimDAC'],
                        int(isHotChan or dict_vfatTrimMaskData[vfat][chan]['mask'])))
        else:
            confF.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I:maskReason/I\n')
            if args.debug:
                print('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:mask/I\n')
            for vfat in range (0,nVFATS):
                if vfat not in dict_chipID:
                    continue
                vfatChanArray = hot_channels[ hot_channels['vfatN'] == vfat ]
                for chan in range(0,maxChans):
                    isHotChan = vfatChanArray[ vfatChanArray['vfatCH'] == chan ]['mask']
                    if args.debug:
                        print('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(
                            vfat,
                            dict_chipID[vfat],
                            chan,
                            dict_vfatTrimMaskData[vfat][chan]['trimDAC'],
                            dict_vfatTrimMaskData[vfat][chan]['trimPolarity'],
                            int(isHotChan or dict_vfatTrimMaskData[vfat][chan]['mask']),
                            dict_vfatTrimMaskData[vfat][chan]['maskReason']))
                    confF.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(
                        vfat,
                        dict_chipID[vfat],
                        chan,
                        dict_vfatTrimMaskData[vfat][chan]['trimDAC'],
                        dict_vfatTrimMaskData[vfat][chan]['trimPolarity'],
                        int(isHotChan or dict_vfatTrimMaskData[vfat][chan]['mask']),
                        dict_vfatTrimMaskData[vfat][chan]['maskReason']))

        confF.close()
        pass

    inFile.Close()

    # Do we return analyzed TTree?
    from multiprocessing import current_process
    if (current_process().name == 'MainProcess'):
        return thrAnaTree
    else:
        # multiprocessing cannot handle the thrAnaTree object to be passed back
        # raises a MaybeEncodingError exception; this is because multiprocessing
        # encodes data in 32 bit words.  Seems like TTree objects are encoded with
        # 64 bit words; see: https://bugs.python.org/issue17560
        return

def calibrateThrDACStar(inputs):
    """
    Wrapper to be used with multiprocessing.Pool methods
    See: https://stackoverflow.com/questions/5442910/python-multiprocessing-pool-map-for-multiple-arguments

    When moving to python 3.X we should use the Pool::starmap function and not this wrapper:
    see: https://stackoverflow.com/a/5442981
    """
    return calibrateThrDAC(*inputs)

from anaInfo import maxEffPedPercentDefault, highNoiseCutDefault, deadChanCutLowDefault, deadChanCutHighDefault, numOfGoodChansMinDefault 

def calibrateThrDAC(args):
    """
    Calibrates CFG_THR_X_DAC, for X = {ARM,ZCC}, in terms of charge units from a series of scurve measurements.

    Returns either 0 or an error code, see: https://docs.python.org/2/library/os.html#process-management

    The single argument "args" is intended to be a namespace which has attributes among those listed below.  

        inputFile         - Filename of a file in the "Three Column Format," see parseListOfScanDatesFile from
                                 gempython.gemplotting.utils.anautilities, where each entry after the column header
                                 is an analyzed scurve file taken at a different CFG_THR_X_DAC for a (shelf,slot,link).
        fitRange          - Two comma separated integers which specify the range of 'CFG_THR_*_DAC' to use in 
                                 fitting when deriving the calibration curve.
        listOfVFATs       - If provided vfatID will be taken from this file rather than scurveFitTree in input
                                 analyzed scurve files defined in inputFile.  This is a tab delimited file, first line
                                 is a column header, subsequent lines specifying respectively VFAT position and chipID.
                                 Lines beginning with the "#" character will be skipped.
        noLeg             - Do not draw a TLegend on the output plots.
        outputDir         - String specifying location of output files, if None then $ELOG_PATH will be used
        savePlots         - Make a '*.png' file for all plots that will be saved in the output TFile
        numOfGoodChansMin - If the number of good channels associated with an armDacVal point is less than numOfGoodChansMin, 
                                then that armDacVal point is not used. This is criterion is applied separately for each VFAT.
        maxEffPedPercent  - If channel effPed > maxEffPedPercent, then the channel is marked as bad. 
        highNoiseCut      - If scurve_sigma > highNoiseCut, then the channel is marked as bad.
        deadChanCutLow    - If deadChanCutLow < scurve_sigma < deadChanCutHigh, then the channel is marked as bad.
        deadChanHighLow   - If deadChanCutLow < scurve_sigma < deadChanCutHigh, then the channel is marked as bad.
    """

    if not hasattr(args,"inputFile"):
        print("No inputFile provided to calibrateThrDac")
        import os
        exit(os.EX_NOINPUT)

    if not hasattr(args,"fitRange"):
        args.fitRange = [0, 255]
    else:
        args.fitRange = [int(item) for item in args.fitRange.split(",")]        

    if not hasattr(args,"listofVFATs"):
        args.listOfVFATs = None

    if not hasattr(args,"numOfGoodChansMin"):
        args.numOfGoodChansMin=numOfGoodChansMinDefault 
        
    if not hasattr(args,"maxEffPedPercent"):
        args.maxEffPedPercent=maxEffPedPercentDefault

    if not hasattr(args,"highNoiseCut"):
        args.highNoiseCut=highNoiseCutDefault

    if not hasattr(args,"deadChanCutLow"):
        args.deadChanCutLow=deadChanCutLowDefault

    if not hasattr(args,"deadChanCutHigh"):
        args.deadChanCutHigh=deadChanCutHighDefault

    if not hasattr(args,"noLeg"):
        args.noLeg=False

    if not hasattr(args,"outputDir"):
        from gempython.gemplotting.utils.anautilities import getElogPath
        args.outputDir = getElogPath()

    if not hasattr(args,"savePlots"):
        args.savePlots=False

    if not hasattr(args,"debug"):
        args.debug=False                        
    
    # Suppress all pop-ups from ROOT
    import ROOT as r
    r.gROOT.SetBatch(True)

    # Redirect sys.stdout and sys.stderr if necessary 
    from gempython.gemplotting.utils.multiprocUtils import redirectStdOutAndErr
    redirectStdOutAndErr("anaUltraThreshold",args.outputDir)

    # Get info from input file
    from gempython.gemplotting.utils.anautilities import getCyclicColor, getDirByAnaType, filePathExists, parseListOfScanDatesFile
    parsedTuple = parseListOfScanDatesFile(args.inputFile)
    listChamberAndScanDate = parsedTuple[0]
    thrDacName = parsedTuple[1]
    chamberName = listChamberAndScanDate[0][0]

    ##### FIXME
    gemType = chamberName[:chamberName.find("-")].lower()
    # ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    from gempython.gemplotting.mapping.chamberInfo import CHANNELS_PER_VFAT as maxChans

    # Do we load an optional vfat serial number table? (e.g. chips did not have serial number in efuse burned in)
    import numpy as np
    import root_numpy as rp
    if args.listOfVFATs is not None:
        try:
            mapVFATPos2VFATSN = np.loadtxt(
                        fname = args.listOfVFATs,
                        dtype={'names':('vfatN', 'serialNum'),
                                'formats':('u4', 'u4')},
                        skiprows=1,
                    )
        except IOError as err:
            print('{0} does not seem to exist, is not readable, or does not have the right format'.format(args.listOfVFATs))
            print(type(err))
            return os.EX_NOINPUT
    else:
        mapVFATPos2VFATSN = np.zeros(nVFATS,dtype={'names':('vfatN', 'serialNum'),'formats':('u4', 'u4')})

    # Get list of THR DAC values
    listOfThrValues = []
    for infoTuple in listChamberAndScanDate:
        listOfThrValues.append(infoTuple[2])
    listOfThrValues.sort()

    # Determine step size in THR DAC values
    # This is for making box plots
    deltaBins = np.diff(listOfThrValues)
    uniqueDeltas = np.unique(deltaBins)
    if len(uniqueDeltas) == 1:
        stepSize = np.unique(deltaBins)
        binMin = min(listOfThrValues)-stepSize*0.5
        binMax = max(listOfThrValues)+stepSize*0.5
        nBins = len(listOfThrValues)

    # Make containers
    # In each case where vfat position is used as a key, the value of -1 is the sum over the entire detector
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_gScurveMean = ndict() #Stores TGraphErrors objects. Outer key is CFG_THR_*_DAC value; Inner key follows vfat position
    dict_gScurveSigma = ndict()
    dict_funcScurveMean = ndict()
    dict_funcScurveSigma = ndict()

    dict_nBadChannels = ndict() # Stores the number of bad channels for a VFAT
    
    dict_mGraphScurveMean = {} # Key is VFAT position, stores the dict_gScurveMean[*][vfat] for a given vfat
    dict_mGraphScurveSigma = {}
    dict_ScurveMeanVsThrDac = {} # Key is VFAT position
    dict_ScurveMeanVsThrDac_BoxPlot = {} # Key is VFAT position
    dict_ScurveSigmaVsThrDac = {}
    dict_ScurveSigmaVsThrDac_BoxPlot = {}

    legArmDacValues = r.TLegend(0.5,0.5,0.9,0.9)

    # Get the plots from all files
    from gempython.gemplotting.utils.anaInfo import tree_names
    for idx,infoTuple in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType("scurve", infoTuple[0])
        if not filePathExists(dirPath, infoTuple[1]):
            raise IOError("calibrateThrDAC(): File {0}/{1} does not exist or is not readable".format(dirPath, infoTuple[1]))
        filename = "{0}/{1}/{2}".format(dirPath, infoTuple[1], tree_names["scurveAna"][0])

        # Load the file
        r.TH1.AddDirectory(False)
        scanFile = r.TFile(filename,"READ")

        if not scanFile.IsOpen():
            raise IOError("calibrateThrDAC(): File {0} is not open or is not readable; please check input list of scandates: {1}".format(filename,args.inputFile))
        if scanFile.IsZombie():
            raise IOError("calibrateThrDAC(): File {0} is a zombie; consider removing this from your input list of scandates: {1}".format(filename,args.inputFile))

        # Determine vfatID
        list_bNames = ['vfatN','vfatID']
        array_vfatData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)
        array_vfatData = np.unique(array_vfatData)

        import os
        # Get scurve data for this arm dac value (used for boxplots)
        list_bNames = ['noise', 'threshold', 'vfatN', 'vthr', 'ped_eff']
        scurveFitData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)

        #remove channels that fail quality cuts
        scurveFitMask1 = np.logical_or(scurveFitData['noise'] < args.deadChanCutLow,scurveFitData['noise'] > args.deadChanCutHigh)
        scurveFitMask2 = scurveFitData['noise'] < args.highNoiseCut
        scurveFitMask3 = scurveFitData['ped_eff'] < args.maxEffPedPercent
        #following what is done in the scurve analysis script, 
        #we also remove scurve fits in which the noise or the threshold are equal to their initial values
        scurveFitMask4 = np.logical_and(scurveFitData['noise'] != 0,scurveFitData['threshold'] != 0)

        for vfat in range(-1,nVFATS):
            if vfat == -1:
                dict_nBadChannels[vfat][infoTuple[2]]["DeadChannel"] = len(scurveFitData[scurveFitMask1 == False])
                dict_nBadChannels[vfat][infoTuple[2]]["HighNoise"] = len(scurveFitData[scurveFitMask2 == False])
                dict_nBadChannels[vfat][infoTuple[2]]["HighEffPed"] = len(scurveFitData[scurveFitMask3 == False])
                dict_nBadChannels[vfat][infoTuple[2]]["FitAtInitVal"] = len(scurveFitData[scurveFitMask4 == False])
            else:
                scurveFitMaskVfat = scurveFitData["vfatN"] == vfat
                dict_nBadChannels[vfat][infoTuple[2]]["DeadChannel"] = maxChans-len(scurveFitData[np.logical_and(scurveFitMask1,scurveFitMaskVfat)])
                dict_nBadChannels[vfat][infoTuple[2]]["HighNoise"] = maxChans-len(scurveFitData[np.logical_and(scurveFitMask2,scurveFitMaskVfat)])
                dict_nBadChannels[vfat][infoTuple[2]]["HighEffPed"] = maxChans-len(scurveFitData[np.logical_and(scurveFitMask3,scurveFitMaskVfat)])
                dict_nBadChannels[vfat][infoTuple[2]]["FitAtInitVal"] = maxChans-len(scurveFitData[np.logical_and(scurveFitMask4,scurveFitMaskVfat)])

        scurveFitMask = np.logical_and(np.logical_and(np.logical_and(scurveFitMask1,scurveFitMask2),scurveFitMask3),scurveFitMask4)
        scurveFitData = scurveFitData[scurveFitMask] 
        
        ###################
        # Get and fit individual distributions
        ###################
        for vfat in range(-1,nVFATS):
            if vfat == -1:
                suffix = "All"
                loadPath = suffix
                directory = "Summary"
            else:
                if args.listOfVFATs is not None:
                    vfatID = mapVFATPos2VFATSN[mapVFATPos2VFATSN['vfatN'] == vfat]
                else:
                    if len(array_vfatData[array_vfatData['vfatN'] == vfat]) > 0:
                        mapVFATPos2VFATSN[vfat]['vfatN'] = vfat
                        mapVFATPos2VFATSN[vfat]['serialNum'] = array_vfatData[array_vfatData['vfatN'] == vfat]['vfatID']
                    else:
                        mapVFATPos2VFATSN[vfat]['vfatN'] = vfat
                        mapVFATPos2VFATSN[vfat]['serialNum'] = 0
                suffix = "vfatN{0}_vfatID{1}".format(vfat,mapVFATPos2VFATSN[vfat]['serialNum'])
                loadPath = "vfat{0}".format(vfat)
                directory = loadPath.upper()

            # Make the TMultiGraph Objects
            if idx == 0:
                # Scurve Mean
                dict_mGraphScurveMean[vfat] = r.TMultiGraph("mGraph_ScurveMeanByThrDac_{0}".format(suffix),suffix)

                dict_ScurveMeanVsThrDac[vfat] = r.TGraphErrors()
                dict_ScurveMeanVsThrDac[vfat].SetTitle(suffix)
                dict_ScurveMeanVsThrDac[vfat].SetName("gScurveMean_vs_{0}_{1}".format(thrDacName,suffix))
                dict_ScurveMeanVsThrDac[vfat].SetMarkerStyle(23)

                if len(uniqueDeltas) == 1:
                    #placeholder
                    dict_ScurveMeanVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveMean_vs_{0}_{1}".format(thrDacName,suffix),suffix,nBins,binMin,binMax,1002,-0.1,100.1)
                else:
                    dict_ScurveMeanVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveMean_vs_{0}_{1}".format(thrDacName,suffix),suffix,256,-0.5,255.5,1002,-0.1,100.1)
                dict_ScurveMeanVsThrDac_BoxPlot[vfat].SetXTitle(thrDacName)
                dict_ScurveMeanVsThrDac_BoxPlot[vfat].SetYTitle("Scurve Mean #left(fC#right)")

                # Scurve Sigma
                dict_mGraphScurveSigma[vfat] = r.TMultiGraph("mGraph_ScurveSigmaByThrDac_{0}".format(suffix),suffix)

                dict_ScurveSigmaVsThrDac[vfat] = r.TGraphErrors()
                dict_ScurveSigmaVsThrDac[vfat].SetTitle(suffix)
                dict_ScurveSigmaVsThrDac[vfat].SetName("gScurveSigma_vs_{0}_{1}".format(thrDacName,suffix))
                dict_ScurveSigmaVsThrDac[vfat].SetMarkerStyle(23)

                if len(uniqueDeltas) == 1:
                    dict_ScurveSigmaVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveSigma_vs_{0}_{1}".format(thrDacName,suffix),suffix,nBins,binMin,binMax,504,-0.1,25.1)
                else:
                    dict_ScurveSigmaVsThrDac_BoxPlot[vfat] = r.TH2F("h_ScurveSigma_vs_{0}_{1}".format(thrDacName,suffix),suffix,256,-0.5,255.5,504,-0.1,25.1)
                dict_ScurveSigmaVsThrDac_BoxPlot[vfat].SetXTitle(thrDacName)
                dict_ScurveSigmaVsThrDac_BoxPlot[vfat].SetYTitle("Scurve Sigma #left(fC#right)")

            if vfat > -1:    
                scurveFitDataThisVfat = scurveFitData[scurveFitData["vfatN"] == vfat]
            else:
                scurveFitDataThisVfat = scurveFitData

            #define histograms which will hold the per-VFAT scurve mean and scurve sigma distributions
            #when there is no data, we create a dummy histogram which will not be filled with anything
            if len(scurveFitDataThisVfat) != 0:
                thisVFAT_ThreshMean = np.mean(scurveFitDataThisVfat["threshold"])
                thisVFAT_ThreshStd = np.std(scurveFitDataThisVfat["threshold"])
                thisVFAT_ENCMean = np.mean(scurveFitDataThisVfat["noise"])
                thisVFAT_ENCStd = np.std(scurveFitDataThisVfat["noise"])
            else:    
                thisVFAT_ThreshMean = 0 #dummy value
                thisVFAT_ThreshStd = 1 #dummy value
                thisVFAT_ENCMean = 0 #dummy value
                thisVFAT_ENCStd = 1 #dummy value
                
            histThresh = r.TH1F("scurveMean_vfat{0}".format(vfat),"VFAT {0};S-Curve Mean #left(fC#right);N".format(vfat), 
                                40, thisVFAT_ThreshMean - 5. * thisVFAT_ThreshStd, thisVFAT_ThreshMean + 5. * thisVFAT_ThreshStd )
            histENC = r.TH1F("scurveSigma_vfat{0}".format(vfat),"VFAT {0};S-Curve Sigma #left(fC#right);N".format(vfat),
                                 40, thisVFAT_ENCMean - 5. * thisVFAT_ENCStd, thisVFAT_ENCMean + 5. * thisVFAT_ENCStd )

            #discard armDacVal points with too few good channels
            if len(scurveFitDataThisVfat) < args.numOfGoodChansMin:
                continue

            #fill histograms with the scurve means and the scurve sigmas that pass the quality cuts            
            for idy in range(0,len(scurveFitDataThisVfat)):
                scurveMean = scurveFitDataThisVfat[idy]['threshold']
                scurveSigma = scurveFitDataThisVfat[idy]['noise']
                histThresh.Fill(scurveMean)
                histENC.Fill(scurveSigma)

            ###################
            ### Scurve Mean ###
            ###################
            #convert TH1F to TGraph for fitting           
            dict_gScurveMean[infoTuple[2]][vfat] = r.TGraphErrors(histThresh)

            if vfat > -1:
                dict_gScurveMean[infoTuple[2]][vfat].SetName("gScurveMeanDist_{0}_thrDAC{1}".format(suffix,infoTuple[2]))
            else:
                dict_gScurveMean[infoTuple[2]][vfat].SetName("{0}_thrDAC{1}".format(dict_gScurveMean[infoTuple[2]][vfat].GetName(),infoTuple[2]))

            #Set style of TGraphErrors
            dict_gScurveMean[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerStyle(21)
            dict_gScurveMean[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Declare the fit function
            arrayX = np.array(dict_gScurveMean[infoTuple[2]][vfat].GetX())
            dict_funcScurveMean[infoTuple[2]][vfat] = r.TF1(
                    "func_{0}".format((dict_gScurveMean[infoTuple[2]][vfat].GetName()).strip('g')),
                    "gaus",
                    np.min(arrayX),
                    np.max(arrayX))

            # Set style of TF1
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineWidth(2)
            dict_funcScurveMean[infoTuple[2]][vfat].SetLineStyle(3)
            dict_funcScurveMean[infoTuple[2]][vfat].SetParLimits(1,0,100) #Limit mean position to be physical

            # Fit
            dict_gScurveMean[infoTuple[2]][vfat].Fit(dict_funcScurveMean[infoTuple[2]][vfat],"QR")

            # Add to MultiGraph
            dict_mGraphScurveMean[vfat].Add(dict_gScurveMean[infoTuple[2]][vfat])

            # Add point to calibration curve
            dict_ScurveMeanVsThrDac[vfat].SetPoint(
                    dict_ScurveMeanVsThrDac[vfat].GetN(),
                    infoTuple[2],
                    dict_funcScurveMean[infoTuple[2]][vfat].GetParameter("Mean"))
            dict_ScurveMeanVsThrDac[vfat].SetPointError(
                    dict_ScurveMeanVsThrDac[vfat].GetN()-1,
                    0,
                    dict_funcScurveMean[infoTuple[2]][vfat].GetParameter("Sigma"))

            ####################
            ### Scurve Sigma ###
            ####################
            #convert TH1F to TGraphErrors for fitting                       
            dict_gScurveSigma[infoTuple[2]][vfat] = r.TGraphErrors(histENC)

            if vfat > -1:
                dict_gScurveSigma[infoTuple[2]][vfat].SetName("gScurveSigmaDist_{0}_thrDAC{1}".format(suffix,infoTuple[2]))
            else:
                dict_gScurveSigma[infoTuple[2]][vfat].SetName("{0}_thrDAC{1}".format(dict_gScurveSigma[infoTuple[2]][vfat].GetName(),infoTuple[2]))

            #Set style of TGraphErrors
            dict_gScurveSigma[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerStyle(21)
            dict_gScurveSigma[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Get the fitted function
            arrayX = np.array(dict_gScurveSigma[infoTuple[2]][vfat].GetX())
            dict_funcScurveSigma[infoTuple[2]][vfat] = r.TF1(
                    "func_{0}".format((dict_gScurveSigma[infoTuple[2]][vfat].GetName()).strip('g')),
                    "gaus",
                    np.min(arrayX),
                    np.max(arrayX))

            #prevents the fit from going crazy and returning a mean of 10^300, which causes pyroot to crash later on
            dict_funcScurveSigma[infoTuple[2]][vfat].SetParLimits(dict_funcScurveSigma[infoTuple[2]][vfat].GetParNumber("Mean"),np.min(arrayX),np.max(arrayX))
            
            # Set style of TF1
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineWidth(2)
            dict_funcScurveSigma[infoTuple[2]][vfat].SetLineStyle(3)

            # Fit
            dict_gScurveSigma[infoTuple[2]][vfat].Fit(dict_funcScurveSigma[infoTuple[2]][vfat],"QR")

            # Add to MultiGraph
            dict_mGraphScurveSigma[vfat].Add(dict_gScurveSigma[infoTuple[2]][vfat])

            # Add point to calibration curve
            dict_ScurveSigmaVsThrDac[vfat].SetPoint(
                    dict_ScurveSigmaVsThrDac[vfat].GetN(),
                    infoTuple[2],
                    dict_funcScurveSigma[infoTuple[2]][vfat].GetParameter("Mean"))
            dict_ScurveSigmaVsThrDac[vfat].SetPointError(
                    dict_ScurveSigmaVsThrDac[vfat].GetN()-1,
                    0,
                    dict_funcScurveSigma[infoTuple[2]][vfat].GetParameter("Sigma"))

            ###################
            # Make an entry in the TLegend
            ###################
            if vfat == 0:
                legArmDacValues.AddEntry(
                        dict_gScurveSigma[infoTuple[2]][vfat],
                        "{0} = {1}".format(thrDacName, infoTuple[2]),
                        "LPE")

        ######################
        ### Fill Box Plots ###
        ######################
        for idx in range(0,len(scurveFitData)):
            scurveMean = scurveFitData[idx]['threshold']
            scurveSigma = scurveFitData[idx]['noise']
            thrDacVal = scurveFitData[idx]['vthr']
            vfatN = scurveFitData[idx]['vfatN']

            # All VFATs
            dict_ScurveMeanVsThrDac_BoxPlot[-1].Fill(thrDacVal,scurveMean)
            dict_ScurveSigmaVsThrDac_BoxPlot[-1].Fill(thrDacVal,scurveSigma)

            # Per VFAT
            dict_ScurveMeanVsThrDac_BoxPlot[vfatN].Fill(thrDacVal,scurveMean)
            dict_ScurveSigmaVsThrDac_BoxPlot[vfatN].Fill(thrDacVal,scurveSigma)

    ###################
    # Make output calibration file
    ###################
    try:
        calThrDacFile = open("{0}/calFile_{2}_{1}.txt".format(args.outputDir,chamberName,thrDacName),'w')
    except IOError as e:
        print("Caught Exception: {0}".format(e))
        print("Unabled to open file '{0}/calFile_{2}_{1}.txt'".format(args.outputDir,chamberName,thrDacName))
        print("Perhaps the path does not exist or you do not have write permissions?")
        return os.EX_IOERR
    calThrDacFile.write("vfatN/I:coef4/F:coef3/F:coef2/F:coef1/F:coef0/F\n")

    ###################
    # Make output ROOT file
    ###################
    outFileName = "{0}/calFile_{2}_{1}.root".format(args.outputDir,chamberName,thrDacName)
    outFile = r.TFile(outFileName,"RECREATE")

    # Plot Containers
    dict_canvScurveMeanByThrDac = {}
    dict_canvScurveSigmaByThrDac = {}

    dict_canvScurveMeanVsThrDac = {}
    dict_canvScurveSigmaVsThrDac = {}

    dict_canvScurveMeanVsThrDac_BoxPlot = {}
    dict_canvScurveSigmaVsThrDac_BoxPlot = {}

    dict_funcScurveMeanVsThrDac = {}

    ###################
    # Now Make plots & Fit DAC Curves
    ###################
    if args.debug:
        print("| vfatN | coef4 | coef3 | coef2 | coef1 | coef0 | noise | noise_err |")
        print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :-------: |")
    for vfat in range(-1,nVFATS):
        if vfat == -1:
            suffix = "All"
            directory = "Summary"
        else:
            suffix = "vfatN{0}_vfatID{1}".format(vfat,mapVFATPos2VFATSN[vfat]['serialNum'])
            directory = "VFAT{0}".format(vfat)

        thisDirectory = outFile.mkdir(directory)
        RawDataDir = thisDirectory.mkdir("RawData")
        RawDataDirMean = RawDataDir.mkdir("ScurveMean")
        RawDataDirSigma = RawDataDir.mkdir("ScurveSigma")
        for idx,infoTuple in enumerate(listChamberAndScanDate):
            if vfat in dict_gScurveMean[infoTuple[2]]:
                RawDataDirMean.cd()
                dict_gScurveMean[infoTuple[2]][vfat].Write()
            if vfat in dict_gScurveSigma[infoTuple[2]]:    
                RawDataDirSigma.cd()
                dict_gScurveSigma[infoTuple[2]][vfat].Write()
        thisDirectory.cd()

        # Mean by CFG_THR_*_DAC
        dict_canvScurveMeanByThrDac[vfat] = r.TCanvas("canvScurveMeanByThrDac_{0}".format(suffix),"Scurve Mean by THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanByThrDac[vfat].cd()
        dict_mGraphScurveMean[vfat].Draw("APE1")
        dict_mGraphScurveMean[vfat].GetXaxis().SetRangeUser(0,80)
        dict_mGraphScurveMean[vfat].GetXaxis().SetTitle("Scurve Mean #left(fC#right)")
        dict_mGraphScurveMean[vfat].Draw("APE1")
        dict_mGraphScurveMean[vfat].Write()

        # Sigma by CFG_THR_*_DAC
        dict_canvScurveSigmaByThrDac[vfat] = r.TCanvas("canvScurveSigmaByThrDac_{0}".format(suffix),"Scurve Sigma by THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaByThrDac[vfat].cd()
        dict_mGraphScurveSigma[vfat].Draw("APE1")
        dict_mGraphScurveSigma[vfat].GetXaxis().SetRangeUser(0,5)
        dict_mGraphScurveSigma[vfat].GetXaxis().SetTitle("Scurve Sigma #left(fC#right)")
        dict_mGraphScurveSigma[vfat].Draw("APE1")
        dict_mGraphScurveSigma[vfat].Write()

        thrDacIndexPairs = []
        for i in range(0,dict_ScurveMeanVsThrDac[vfat].GetN()):
            thrDacVal = r.Double()
            scurveMean = r.Double()
            dict_ScurveMeanVsThrDac[vfat].GetPoint(i,thrDacVal,scurveMean)
            thrDacIndexPairs.append([thrDacVal,i])

        thrDacIndexPairs.sort()

        #remove THR DAC values where there appear to be pedestal effects
        tgraph_scurveSigmaHighThrDacVal=r.TGraphErrors(5)
        scurveSigmaMeanHighThrDacVal = 0
        for i in range(len(thrDacIndexPairs)-5,len(thrDacIndexPairs)):
            thrDacVal = r.Double()
            scurveSigma = r.Double()
            dict_ScurveSigmaVsThrDac[vfat].GetPoint(thrDacIndexPairs[i][1],thrDacVal,scurveSigma)
            scurveSigmaError = dict_ScurveSigmaVsThrDac[vfat].GetErrorY(thrDacIndexPairs[i][1])
            tgraph_scurveSigmaHighThrDacVal.SetPoint(i-(len(thrDacIndexPairs)-5),thrDacVal,scurveSigma)
            tgraph_scurveSigmaHighThrDacVal.SetPointError(i-(len(thrDacIndexPairs)-5),0,scurveSigmaError)

        tgraph_scurveSigmaHighThrDacVal.Fit("pol0","Q")
        sigmaHighThrDacPlusError = tgraph_scurveSigmaHighThrDacVal.GetFunction("pol0").GetParameter(0)+tgraph_scurveSigmaHighThrDacVal.GetFunction("pol0").GetParError(0)
        sigmaHighThrDacChiSquaredOverNdof = tgraph_scurveSigmaHighThrDacVal.GetFunction("pol0").GetChisquare()/4.0

        tgraph_scurveMeanVsThrDacForFit = r.TGraphErrors()

        setLastUnremovedScurveMean = False
        for i in range(0,len(thrDacIndexPairs)):
            i = len(thrDacIndexPairs) - 1 - i
            thrDacVal = r.Double()
            scurveSigma = r.Double()
            scurveMean = r.Double()
            dict_ScurveSigmaVsThrDac[vfat].GetPoint(thrDacIndexPairs[i][1],thrDacVal,scurveSigma)
            dict_ScurveMeanVsThrDac[vfat].GetPoint(thrDacIndexPairs[i][1],thrDacVal,scurveMean)
            scurveSigmaError = dict_ScurveSigmaVsThrDac[vfat].GetErrorY(thrDacIndexPairs[i][1])
            scurveMeanError = dict_ScurveMeanVsThrDac[vfat].GetErrorY(thrDacIndexPairs[i][1])
            from gempython.gemplotting.utils.anaInfo import scurveMeanMin, scurveMeanFracErrMin
            if scurveMean < scurveMeanMin or scurveMeanError/scurveMean < scurveMeanFracErrMin:
                continue
            if not setLastUnremovedScurveMean:
                lastUnremovedScurveMean = scurveMean
                setLastUnremovedScurveMean = True
            if (thrDacVal < 50 and sigmaHighThrDacChiSquaredOverNdof < 0.5 and scurveSigma - scurveSigmaError > sigmaHighThrDacPlusError and scurveMean > 6 and scurveMean > lastUnremovedScurveMean) or (scurveMean > 2*lastUnremovedScurveMean):
                continue
            lastUnremovedScurveMean = scurveMean
            tgraph_scurveMeanVsThrDacForFit.SetPoint(tgraph_scurveMeanVsThrDacForFit.GetN(),thrDacVal,scurveMean)
            tgraph_scurveMeanVsThrDacForFit.SetPointError(tgraph_scurveMeanVsThrDacForFit.GetN()-1,0,scurveMeanError)

        #update the fit range
        #this will not affect the fit, it is just for the output plots
        thrDacVal = r.Double()
        scurveMean = r.Double()
        tgraph_scurveMeanVsThrDacForFit.GetPoint(tgraph_scurveMeanVsThrDacForFit.GetN()-1,thrDacVal,scurveMean)
        perVfatFitRange = list(args.fitRange)
        if thrDacVal > perVfatFitRange[0]:
            perVfatFitRange[0] = float(thrDacVal)
        tgraph_scurveMeanVsThrDacForFit.GetPoint(0,thrDacVal,scurveMean)
        if thrDacVal < perVfatFitRange[1]:
            perVfatFitRange[1] = float(thrDacVal)

        # Mean vs CFG_THR_*_DAC
        dict_canvScurveMeanVsThrDac[vfat] = r.TCanvas("canvScurveMeanVsThrDac_{0}".format(suffix),"Scurve Mean vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanVsThrDac[vfat].cd()
        dict_ScurveMeanVsThrDac[vfat].Draw("APE1")
        dict_ScurveMeanVsThrDac[vfat].GetXaxis().SetTitle(thrDacName)
        dict_ScurveMeanVsThrDac[vfat].GetYaxis().SetTitle("Scurve Mean #left(fC#right)")
        dict_ScurveMeanVsThrDac[vfat].Draw("APE1")
        dict_funcScurveMeanVsThrDac[vfat] = r.TF1("func_{0}".format((dict_ScurveMeanVsThrDac[vfat].GetName()).strip('g')),"[0]*x^4+[1]*x^3+[2]*x^2+[3]*x+[4]",min(perVfatFitRange),max(perVfatFitRange))
        #require the first derivative to be positive at the lower boundary of the fit range
        dict_funcScurveMeanVsThrDac[vfat].SetParLimits(3,0,1000000)
        tgraph_scurveMeanVsThrDacForFit.Fit(dict_funcScurveMeanVsThrDac[vfat],"QR")
        dict_ScurveMeanVsThrDac[vfat].Write()
        dict_funcScurveMeanVsThrDac[vfat].Write()

        # Mean vs CFG_THR_*_DAC - Box Plot
        dict_canvScurveMeanVsThrDac_BoxPlot[vfat] = r.TCanvas("canvScurveMeanVsThrDac_BoxPlot_{0}".format(suffix),"Box Plot: Scurve Mean vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveMeanVsThrDac_BoxPlot[vfat].cd()
        dict_ScurveMeanVsThrDac_BoxPlot[vfat].Draw("candle1")
        dict_ScurveMeanVsThrDac_BoxPlot[vfat].Write()

        # Sigma vs CFG_THR_*_DAC
        dict_canvScurveSigmaVsThrDac[vfat] = r.TCanvas("canvScurveSigmaVsThrDac_{0}".format(suffix),"Scurve Sigma vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaVsThrDac[vfat].cd()
        dict_ScurveSigmaVsThrDac[vfat].Draw("APE1")
        dict_ScurveSigmaVsThrDac[vfat].GetXaxis().SetTitle(thrDacName)
        dict_ScurveSigmaVsThrDac[vfat].GetYaxis().SetTitle("Scurve Sigma #left(fC#right)")
        dict_ScurveSigmaVsThrDac[vfat].Draw("APE1")
        func_ScurveSigmaVsThrDac = r.TF1("func_{0}".format((dict_ScurveSigmaVsThrDac[vfat].GetName()).strip('g')),"[0]",min(args.fitRange), max(args.fitRange) )
        dict_ScurveSigmaVsThrDac[vfat].Fit(func_ScurveSigmaVsThrDac,"QR")
        dict_ScurveSigmaVsThrDac[vfat].Write()
        func_ScurveSigmaVsThrDac.Write()

        # Sigma vs CFG_THR_*_DAC - Box Plot
        dict_canvScurveSigmaVsThrDac_BoxPlot[vfat] = r.TCanvas("canvScurveSigmaVsThrDac_BoxPlot_{0}".format(suffix),"Box Plot: Scurve Sigma vs. THR DAC - {0}".format(suffix),700,700)
        dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].cd()
        dict_ScurveSigmaVsThrDac_BoxPlot[vfat].Draw("candle1")
        dict_ScurveSigmaVsThrDac_BoxPlot[vfat].Write()

        # Write CFG_THR_*_DAC calibration file
        calThrDacFile.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
            vfat,
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(0),
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(1),
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(2),
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(3),
            dict_funcScurveMeanVsThrDac[vfat].GetParameter(4))
            )

        # Draw Legend?
        if not args.noLeg:
            dict_canvScurveMeanByThrDac[vfat].cd()
            legArmDacValues.Draw("same")

            dict_canvScurveSigmaByThrDac[vfat].cd()
            legArmDacValues.Draw("same")
            pass

        # Store Canvases
        dict_canvScurveMeanByThrDac[vfat].Write()
        dict_canvScurveSigmaByThrDac[vfat].Write()
        dict_canvScurveMeanVsThrDac[vfat].Write()
        dict_canvScurveSigmaVsThrDac[vfat].Write()
        dict_canvScurveMeanVsThrDac_BoxPlot[vfat].Write()
        dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].Write()

        # Print info to user
        if args.debug:
            vfatOrAll = vfat
            if vfat == -1:
                vfatOrAll == "All"
            print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} |".format(
                vfatOrAll,
                dict_funcScurveMeanVsThrDac[vfat].GetParameter(0),
                dict_funcScurveMeanVsThrDac[vfat].GetParameter(1),
                dict_funcScurveMeanVsThrDac[vfat].GetParameter(2),
                dict_funcScurveMeanVsThrDac[vfat].GetParameter(3),
                dict_funcScurveMeanVsThrDac[vfat].GetParameter(4),
                func_ScurveSigmaVsThrDac.GetParameter(0),
                func_ScurveSigmaVsThrDac.GetParError(1))
                )

    print("| vfatN | armDacVal | Dead Chan | High Noise | High Eff Ped | Fit At Init Val |")
    print("| :---: | :-------: | :-------: | :--------: | :----------: | :-------------: |")

    for vfat in range(-1,nVFATS):
        for infoTuple in listChamberAndScanDate:
            if vfat not in dict_nBadChannels or infoTuple[2] not in dict_nBadChannels[vfat]:
                continue
            vfatnOrAll = str(vfat)
            if vfatnOrAll == "-1":
                vfatnOrAll = "All"
            print('| {0} | {1} | {2} | {3} | {4} | {5} |'.format(
                vfatnOrAll,
                infoTuple[2],
                dict_nBadChannels[vfat][infoTuple[2]]["DeadChannel"],
                dict_nBadChannels[vfat][infoTuple[2]]["HighNoise"],
                dict_nBadChannels[vfat][infoTuple[2]]["HighEffPed"],
                dict_nBadChannels[vfat][infoTuple[2]]["FitAtInitVal"]))

    if args.savePlots:
        for vfat in range(-1,nVFATS):
            dict_canvScurveMeanByThrDac[vfat].SaveAs("{0}/{1}.png".format(args.outputDir,dict_canvScurveMeanByThrDac[vfat].GetName()))
            dict_canvScurveSigmaByThrDac[vfat].SaveAs("{0}/{1}.png".format(args.outputDir,dict_canvScurveSigmaByThrDac[vfat].GetName()))
            dict_canvScurveMeanVsThrDac[vfat].SaveAs("{0}/{1}.png".format(args.outputDir,dict_canvScurveMeanVsThrDac[vfat].GetName()))
            dict_canvScurveSigmaVsThrDac[vfat].SaveAs("{0}/{1}.png".format(args.outputDir,dict_canvScurveSigmaVsThrDac[vfat].GetName()))
            dict_canvScurveMeanVsThrDac_BoxPlot[vfat].SaveAs("{0}/{1}.png".format(args.outputDir,dict_canvScurveMeanVsThrDac_BoxPlot[vfat].GetName()))
            dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].SaveAs("{0}/{1}.png".format(args.outputDir,dict_canvScurveSigmaVsThrDac_BoxPlot[vfat].GetName()))

    from gempython.gemplotting.utils.anautilities import getSummaryCanvas, addPlotToCanvas
    # Make summary canvases, always save these
    canvScurveMeanByThrDac_Summary = getSummaryCanvas(dict_mGraphScurveMean, name="canvScurveMeanByThrDac_Summary", drawOpt="APE1", gemType=gemType)
    canvScurveSigmaByThrDac_Summary = getSummaryCanvas(dict_mGraphScurveSigma, name="canvScurveSigmaByThrDac_Summary", drawOpt="APE1", gemType=gemType)
    canvScurveMeanVsThrDac_Summary = getSummaryCanvas(dict_ScurveMeanVsThrDac, name="canvScurveMeanVsThrDac_Summary", drawOpt="APE1", gemType=gemType)
    canvScurveMeanVsThrDac_Summary = addPlotToCanvas(canv=canvScurveMeanVsThrDac_Summary, content=dict_funcScurveMeanVsThrDac, gemType=gemType)
    canvScurveSigmaVsThrDac_Summary = getSummaryCanvas(dict_ScurveSigmaVsThrDac, name="canvScurveSigmaVsThrDac_Summary", drawOpt="APE1", gemType=gemType)
    canvScurveMeanVsThrDac_BoxPlot_Summary = getSummaryCanvas(dict_ScurveMeanVsThrDac_BoxPlot, name="canvScurveMeanVsThrDac_BoxPlot_Summary", drawOpt="candle1", gemType=gemType)
    canvScurveSigmaVsThrDac_BoxPlot_Summary = getSummaryCanvas(dict_ScurveSigmaVsThrDac_BoxPlot, name="canvScurveSigmaVsThrDac_BoxPlot_Summary", drawOpt="candle1", gemType=gemType)

    # Draw Legend?
    if not args.noLeg:
        canvScurveMeanByThrDac_Summary.cd(1)
        legArmDacValues.Draw("same")

        canvScurveSigmaByThrDac_Summary.cd(1)
        legArmDacValues.Draw("same")

    # Save summary canvases (alwasys)
    print("\nSaving Summary TCanvas Objects")
    canvScurveMeanByThrDac_Summary.SaveAs("{0}/{1}.png".format(args.outputDir,canvScurveMeanByThrDac_Summary.GetName()))
    canvScurveSigmaByThrDac_Summary.SaveAs("{0}/{1}.png".format(args.outputDir,canvScurveSigmaByThrDac_Summary.GetName()))
    canvScurveMeanVsThrDac_Summary.SaveAs("{0}/{1}.png".format(args.outputDir,canvScurveMeanVsThrDac_Summary.GetName()))
    canvScurveSigmaVsThrDac_Summary.SaveAs("{0}/{1}.png".format(args.outputDir,canvScurveSigmaVsThrDac_Summary.GetName()))
    canvScurveMeanVsThrDac_BoxPlot_Summary.SaveAs("{0}/{1}.png".format(args.outputDir,canvScurveMeanVsThrDac_BoxPlot_Summary.GetName()))
    canvScurveSigmaVsThrDac_BoxPlot_Summary.SaveAs("{0}/{1}.png".format(args.outputDir,canvScurveSigmaVsThrDac_BoxPlot_Summary.GetName()))

    # Close output files
    outFile.Close()
    calThrDacFile.close()

    print("\nYour calibration file is located in:")
    print("\n\t{0}/calFile_{2}_{1}.txt\n".format(args.outputDir,chamberName,thrDacName))

    print("You can find all ROOT objects in:")
    print("\n\t{0}/calFile_{2}_{1}.root\n".format(args.outputDir,chamberName,thrDacName))

    print("You can find all plots in:")
    print("\n\t{0}\n".format(args.outputDir))

    return 0

def sbitRateAnalysis(chamber_config, rateTree, cutOffRate=0.0, debug=False, outfilename='SBitRatePlots.root', scandate='noscandate'):
    """
    Analyzes a scan taken with sbitRateScanAllLinks(...) from gempython.vfatqc.utils.scanUtils

    Returns a tuple (boolean,dictionary) where the dictionary returned is:

        dict_dacValsBelowCutOff[dacName][ohKey][vfat] = value

    Where ohKey is a tuple of (shelf,slot,link) providing the mapping for uTCA shelf -> slot -> link mapping.
    Here dacName are the values stored in the "nameX" TBranch of the input TTree.
    And value is the value of dacName for which the SBIT rate is below the cutOffRate.

    The boolean returned states whether the channelOR (false) or perchannel (true) analysis was performed

    Additional input parameters are:

        chamber_config  - chamber_config dictionary
        debug           - Prints additional debugging information
        rateTree        - instance of gemSbitRateTreeStructure
        cutOffRate      - Theshold rate (in Hz) described above
        outfilename     - Name of output TFile to be created
        scandate        - Either a string 'noscandate' or an a datetime object formated as YYYY.MM.DD.hh.mm, e.g
                          returned from "datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")"
    """

    # Get paths
    from gempython.gemplotting.utils.anautilities import getDataPath, getElogPath
    dataPath = getDataPath()
    elogPath = getElogPath()

    # Map TPad to correct vfat
    from ..mapping.chamberInfo import chamber_vfatPos2PadIdx
    from tabulate import tabulate

    from gempython.gemplotting.utils.anautilities import findInflectionPts
    from gempython.gemplotting.utils.anautilities import getSummaryCanvas

    # Allow for yellow warning color
    from gempython.utils.gemlogger import printYellow

    # Set default histogram behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    print("Loading info from input TTree")

    # Get the data
    import root_numpy as rp
    import numpy as np

    #for backwards compatibility, handle input trees that do not have a detName branch by finding the detName using the chamber_config
    list_bNames = ['dacValX','link','nameX','rate','shelf','slot','vfatCH','vfatN','detName']
    if not 'detName' in rateTree.GetListOfBranches():
        list_bNames.remove('detName')

    def getDetName(entry):
        if "detName" in np.dtype(entry).names:
            return entry['detName'][0]
        else:
            return chamber_config[(entry['shelf'],entry['slot'],entry['link'])]


    vfatArray = rp.tree2array(tree=rateTree,branches=list_bNames)
    dacNameArray = np.unique(vfatArray['nameX'])

    # channelOR or perchannel?
    vfatChannels = np.unique(vfatArray['vfatCH'])
    if len(vfatChannels) == 1:
        perchannel = False
    else:
        perchannel = True
        pass

    # make the crateMap
    list_bNames.remove('dacValX')
    list_bNames.remove('nameX')
    list_bNames.remove('rate')
    list_bNames.remove('vfatCH')
    list_bNames.remove('vfatN')
    crateMap = np.unique(rp.tree2array(tree=rateTree,branches=list_bNames))

    #map to go from the ohKey to the detector serial number
    detNamesMap = {}
    
    if "detName" in crateMap.dtype.names:
        for entry in crateMap:
            detNamesMap[(entry['shelf'],entry['slot'],entry['link'])] = entry['detName'][0]

    ##### FIXME
    from gempython.gemplotting.mapping.chamberInfo import gemTypeMapping
    if 'gemType' not in rateTree.GetListOfBranches():
        gemType = "ge11"
    else:
        gemType = gemTypeMapping[rp.tree2array(tree=inFile.latTree, branches =[ 'gemType' ] )[0][0]]
    ##### END
    from gempython.tools.hw_constants import vfatsPerGemVariant
    nVFATS = vfatsPerGemVariant[gemType]
    
    # get nonzero VFATs
    dict_nonzeroVFATs = {}
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        arrayMask = np.logical_and(vfatArray['rate'] > 0, vfatArray['link'] == entry['link'])
        arrayMask = np.logical_and(arrayMask, vfatArray['slot'] == entry['slot'])
        arrayMask = np.logical_and(arrayMask, vfatArray['shelf'] == entry['shelf'])
        dict_nonzeroVFATs[ohKey] = np.unique(vfatArray[arrayMask]['vfatN'])

    if debug:
        printYellow("crateMap:\n{0}".format(crateMap))
        printYellow("dacNameArray:\n{0}".format(dacNameArray))

    # make output directories
    from gempython.utils.wrappers import runCommand
    from gempython.gemplotting.utils.anautilities import getDirByAnaType
    for entry in crateMap:
        detName = getDetName(entry)
        if scandate == 'noscandate':
            runCommand(["mkdir", "-p", "{0}/{1}".format(elogPath,detName)])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(elogPath,detName)])
        else:
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", detName)
            else:
                strDirName = getDirByAnaType("sbitRateor", detName)
                pass
            runCommand(["mkdir", "-p", "{0}/{1}".format(strDirName,scandate)])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(strDirName,scandate)])
            if scandate != "current":
                runCommand(["unlink", "{0}/current".format(strDirName)])
                runCommand(["ln","-s","{0}/{1}".format(strDirName,scandate),"{0}/current".format(strDirName)])
            pass
        pass

    # make nested dictionaries
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_Rate1DVsDACNameX = ndict() #[dacName][ohKey][vfat] = TGraphErrors
    dict_vfatCHVsDACNameX_Rate2D = ndict() #[dacName][ohKey][vfat] = TGraph2D

    # initialize a TGraphErrors and a TF1 for each vfat
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            for vfat in range(0,nVFATS+1): #24th VFAT represents "overall case"
                # 1D Distributions
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat] = r.TGraphErrors()
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].SetName("g1D_rate_vs_{0}_vfat{1}".format(dacName.replace("_","-"),vfat))
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetXaxis().SetTitle(dacName)
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetYaxis().SetRangeUser(1e-1,1e8)
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetYaxis().SetTitle("SBIT Rate #left(Hz#right)")
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].SetMarkerStyle(23)
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].SetMarkerSize(0.8)
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].SetLineWidth(2)
                # 2D Distributions
                dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat] = r.TGraph2D()
                dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].SetName("g2D_vfatCH_vs_{0}_rate_vfat{1}".format(dacName.replace("_","-"),vfat))
                dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].GetXaxis().SetTitle(dacName)
                dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].GetYaxis().SetTitle("VFAT Channel")
                dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].GetZaxis().SetTitle("SBIT Rate #left(Hz#right)")
                pass
            pass
        pass
    # create output TFiles
    outputFiles = {}
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])        
        detName = getDetName(entry)
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        if scandate == 'noscandate':
            outputFiles[ohKey] = r.TFile(elogPath+"/"+detName+"/"+outfilename,'recreate')
        else:
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", detName)
            else:
                strDirName = getDirByAnaType("sbitRateor", detName)
                pass
            outputFiles[ohKey] = r.TFile(strDirName+scandate+"/"+outfilename,'recreate')
            pass
        pass
    # Loop over events the tree and fill plots
    print("Looping over stored events in rateTree")
    from math import sqrt
    import traceback, itertools, sys, os
    for event in rateTree:
        ohKey = (event.shelf,event.slot,event.link)
        vfat = event.vfatN

        if vfat not in dict_nonzeroVFATs[ohKey]:
            continue

        #Get the DAC Name in question
        dacName = str(event.nameX.data())

        try:
            if event.vfatCH == 128:
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].SetPoint(
                        dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetN(),
                        event.dacValX,
                        event.rate)
                dict_Rate1DVsDACNameX[dacName][ohKey][vfat].SetPointError(
                        dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetN()-1,
                        0,
                        sqrt(event.rate))
            else:
                dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].SetPoint(
                        dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].GetN(),
                        event.dacValX,
                        event.vfatCH,
                        event.rate)
        except AttributeError:
            # print("Point Number: ", counter) ### variable missing?
            print("event.vfatCH = ", event.vfatCH)
            print("dacName = ", dacName)
            print("ohKey = ", ohKey)
            print("vfat = ", vfat)
            print("dict_Rate1DVsDACNameX[dacName].keys() = ", dict_Rate1DVsDACNameX.keys() )
            print("dict_Rate1DVsDACNameX[dacName][ohKey].keys() = ", dict_Rate1DVsDACNameX[dacName][ohKey].keys() )
            print("dict_Rate1DVsDACNameX[dacName][ohKey][vfat] = ", dict_Rate1DVsDACNameX[dacName][ohKey][vfat] )
            print("dict_Rate1DVsDACNameX = ", dict_Rate1DVsDACNameX)
            traceback.print_exc(file=sys.stdout)
            sys.exit(os.EX_SOFTWARE)

            pass
        pass

    print("Determine when SBIT rate falls below {0} Hz and writing output data".format(cutOffRate))
    #from array import array
    dict_dacValsBelowCutOff = ndict()

    # make a named dictionary to store inflection pts
    dict_dacInflectPts = ndict()

    from gempython.gemplotting.utils.anautilities import getSummaryCanvas

    
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        detName = getDetName(entry)
        # clear the inflection point table for each new link
        inflectTable = []
        # Per VFAT Poosition
        for vfat in range(0, nVFATS):
            thisVFATDir = outputFiles[ohKey].mkdir("VFAT{0}".format(vfat))

            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])

                thisDACDir = thisVFATDir.mkdir(dacName)
                thisDACDir.cd()

                # Get Inflection Points /////////////////////////////////////////////////
                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

                # perchannel case is not supported provide warning
		if perchannel == True :
                    printYellow("WARNING: perchannel case is not supported for knee finding!   Skipping knee finding" )

                # channelor case
                if perchannel == False :
	            dict_dacInflectPts[dacName][ohKey][vfat] = findInflectionPts(dict_Rate1DVsDACNameX[dacName][ohKey][vfat])
                    inflectTable.append([ohKey, vfat, dict_dacInflectPts[dacName][ohKey][vfat][0][0] ])

                dict_dacValsBelowCutOff[dacName][ohKey][vfat] = 255 #default to max
                for point in range(0,dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetN()):
                    dacValX = r.Double()
                    rateVal = r.Double()
                    dict_Rate1DVsDACNameX[dacName][ohKey][vfat].GetPoint(point,dacValX,rateVal)
                    if rateVal <= cutOffRate:
                        dict_dacValsBelowCutOff[dacName][ohKey][vfat] = int(dacValX)
                        break
                    pass

                if perchannel:
                    dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey][vfat].Write()
                else:
                    dict_Rate1DVsDACNameX[dacName][ohKey][vfat].Write()
                    pass
                pass
            pass

        # put inflection points in a table for each different ohKey 
        if perchannel == False:
            print(tabulate(inflectTable, headers = ['Geo Addr', 'VFAT Number', 'ARM DAC Inflection Pt'], tablefmt='orgtbl') )
            if scandate == 'noscandate':
                inflectTableFile = file("{0}/{1}/inflectionPointTable.txt".format(elogPath,detName), "w")
                inflectTableFile.write(tabulate(inflectTable, headers = ['Geo Addr', 'VFAT Number', 'ARM DAC Inflection Pt'], tablefmt='orgtbl') )
            else: 
                inflectTableFile = file("{0}/{1}/inflectionPointTable.txt".format(strDirName,scandate ), "w")
                inflectTableFile.write(tabulate(inflectTable, headers = ['Geo Addr', 'VFAT Number', 'ARM DAC Inflection Pt'], tablefmt='orgtbl') )

        # Make Graphs /////////////////////////////////////////////////////////////////////////////
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        for idx in range(len(dacNameArray)):
            dacName = np.asscalar(dacNameArray[idx])
            if perchannel:
                canv_Summary2D = getSummaryCanvas(dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey], name="canv_Summary_Rate2D_vs_{0}".format(dacName), drawOpt="TRI1", gemType=gemType)
                for vfat in range(1,nVFATS+1):
                    canv_Summary2D.cd(vfat).SetLogz()
            else:
                canv_Summary1D = getSummaryCanvas(dict_Rate1DVsDACNameX[dacName][ohKey], name="canv_Summary_Rate1D_vs_{0}".format(dacName), drawOpt="APE1", gemType=gemType)
                 # make nVFATs TLines
                kneeLine= []
                for vfat in range(0,nVFATS):
                    canv_Summary1D.cd(vfat + 1).SetLogy()

                    # make sure the inflection point is there
                    if dict_dacInflectPts[dacName][ohKey][vfat][0] == None:
                        kneeLine.append(None)
                        continue

                    # make TH1F into TGraph
                    graph = dict_Rate1DVsDACNameX[dacName][ohKey][vfat]
                    if type(graph) == r.TH1F :
                        graph = r.TGraph(graph)

                    # get maximum y value
                    y = graph.GetY()
                    y = np.array(y)
                    ymax = np.amax(y)

                    # Draw a line on the graphs
                    kneeLine.append(r.TLine(dict_dacInflectPts[dacName][ohKey][vfat][0], 10.0, dict_dacInflectPts[dacName][ohKey][vfat][0], ymax) )
                    kneeLine[vfat].SetLineColor(2)
                    kneeLine[vfat].SetVertical()
                    canv_Summary1D.cd(chamber_vfatPos2PadIdx[gemType][vfat] )
                    kneeLine[vfat].Draw()
                canv_Summary1D.Update()

            # Save the graphs
            if scandate == 'noscandate':
                if perchannel:
                    canv_Summary2D.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,detName,canv_Summary2D.GetName()))
                else:
                    canv_Summary1D.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,detName,canv_Summary1D.GetName()))
            else:
                if perchannel:
                    strDirName = getDirByAnaType("sbitRatech", detName)
                    canv_Summary2D.SaveAs("{0}/{1}/{2}.png".format(strDirName,scandate,canv_Summary2D.GetName()))
                else:
                    strDirName = getDirByAnaType("sbitRateor", detName)
                    canv_Summary1D.SaveAs("{0}/{1}/{2}.png".format(strDirName,scandate,canv_Summary1D.GetName()))
                    pass
                pass
            pass
        outputFiles[ohKey].Close()
        pass

    for ohKey,innerDictByVFATKey in dict_dacValsBelowCutOff["THR_ARM_DAC"].iteritems():
        if ohKey in detNamesMap:
            detName = detNamesMap[ohKey]
        else:
            detName = chamber_config[ohKey]                            

        from gempython.utils.gemlogger import printGreen    
            
        if scandate == 'noscandate':
            vfatConfg = open("{0}/{1}/vfatConfig.txt".format(elogPath,detName),'w')
            printGreen("Output Data for {0} can be found in:\n\t{1}/{0}\n".format(detName,elogPath))
        else:    
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", detName)
            else:
                strDirName = getDirByAnaType("sbitRateor", detName)
            vfatConfg = open("{0}/{1}/vfatConfig.txt".format(strDirName,scandate),'w')
            printGreen("Output Data for {0} can be found in:\n\t{1}/{2}\n".format(detName,strDirName,scandate))
            
        vfatConfg.write("vfatN/I:vt1/I:trimRange/I\n")
        for vfat,armDACVal in innerDictByVFATKey.iteritems():
            vfatConfg.write('{0}\t{1}\t{2}\n'.format(vfat, armDACVal,0))
        vfatConfg.close()    
        
    return 
