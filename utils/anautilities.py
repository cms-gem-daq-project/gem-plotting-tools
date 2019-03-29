r"""
``anautilities`` --- Various other utilities
============================================

.. code-block:: python

    import gempython.gemplotting.utils.anautilities

.. moduleauthor:: Brian Dorney <brian.l.dorney@cern.ch>

Utilities for vfatqc scans

Documentation
-------------
"""

from gempython.utils.gemlogger import printYellow

def dacAnalysis(args, dacScanTree, chamber_config, scandate='noscandate'):
    """
    Analyzes DAC scan data to determine nominal bias current/voltage settings for a particular VFAT3 DAC.
    Returns a dictionary where:

        dict_dacVals[dacName][ohKey][vfat] = value

    Where ohKey is a tuple of (shelf,slot,link) providing the mapping for uTCA shelf -> slot -> link mapping

    Here dacName are the values stored in the "nameX" TBranch of the input TTree.

        dacScanTree - Instance of gemDacCalTreeStructure.  Note the "nameY" TBranch must be either "ADC0" or "ADC1"
        chamber_config - chamber_config dictionary
        scandate - Either a string 'noscandate' or an a datetime object formated as YYYY.MM.DD.hh.mm, e.g
                   returned from "datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")"
    """

    # Set default histogram behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    print("Loading info from input TTree")

    import root_numpy as rp
    import numpy as np
    list_bNames = ['dacValY','link','nameX','shelf','slot','vfatN']
    vfatArray = rp.tree2array(tree=dacScanTree,branches=list_bNames)
    dacNameArray = np.unique(vfatArray['nameX'])
    
    # make the crateMap
    list_bNames.remove('dacValY')
    list_bNames.remove('nameX')
    list_bNames.remove('vfatN')
    crateMap = np.unique(rp.tree2array(tree=dacScanTree,branches=list_bNames))

    # get nonzero VFATs
    dict_nonzeroVFATs = {}
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        arrayMask = np.logical_and(vfatArray['dacValY'] > 0, vfatArray['link'] == entry['link'])
        arrayMask = np.logical_and(arrayMask, vfatArray['slot'] == entry['slot'])
        arrayMask = np.logical_and(arrayMask, vfatArray['shelf'] == entry['shelf'])
        dict_nonzeroVFATs[ohKey] = np.unique(vfatArray[arrayMask]['vfatN'])

    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")
    envCheck("ELOG_PATH")

    import os
    dataPath = os.getenv("DATA_PATH")
    elogPath = os.getenv("ELOG_PATH") 
    
    from gempython.utils.wrappers import runCommand
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        if scandate == 'noscandate':
            runCommand(["mkdir", "-p", "{0}/{1}".format(elogPath,chamber_config[ohKey])])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(elogPath,chamber_config[ohKey])])
        else:
            runCommand(["mkdir", "-p", "{0}/{1}/dacScans/{2}".format(dataPath,chamber_config[ohKey],scandate)])
            runCommand(["chmod", "g+rw", "{0}/{1}/dacScans/{2}".format(dataPath,chamber_config[ohKey],scandate)])
            runCommand(["unlink", "{0}/{1}/dacScans/current".format(dataPath,chamber_config[ohKey])])
            runCommand(["ln","-s","{0}/{1}/dacScans/{2}".format(dataPath,chamber_config[ohKey],scandate),"{0}/{1}/dacScans/current".format(dataPath,chamber_config[ohKey])])
            pass
            
    # Determine which DAC was scanned and against which ADC
    adcName = ""
    for event in dacScanTree:
        adcName = str(event.nameY.data())
        break # all entries will be the same

    from gempython.utils.gemlogger import colormsg
    import logging
    if adcName not in ['ADC0', 'ADC1']:
        raise Exception(colormsg("Error: unexpected value of adcName: '%s'"%adcName,logging.ERROR), os.EX_DATAERR)

    from gempython.gemplotting.utils.anaInfo import nominalDacValues, nominalDacScalingFactors
    nominal = {}
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        if dacName not in nominalDacValues.keys():
            raise Exception(colormsg("Error: unexpected DAC Name: '{}'".format(dacName),logging.ERROR), os.EX_DATAERR)
        else:
            nominal[dacName] = nominalDacValues[dacName][0]

            #convert all voltages to mV and currents to uA
            if nominalDacValues[dacName][1] == "V":
                nominal[dacName] *= pow(10.0,3)
            elif nominalDacValues[dacName][1] == 'mV':
                pass
            elif nominalDacValues[dacName][1] == 'uV':
                nominal[dacName] *= pow(10.0,-3)
            elif nominalDacValues[dacName][1] == 'nV':
                nominal[dacName] *= pow(10.0,-6)
            elif nominalDacValues[dacName][1] == "A":
                nominal[dacName] *= pow(10.0,6)
            elif nominalDacValues[dacName][1] == 'mA':
                nominal[dacName] *= pow(10.0,3)
            elif nominalDacValues[dacName][1] == 'uA':
                pass
            elif nominalDacValues[dacName][1] == 'nA':
                nominal[dacName] *= pow(10.0,-3)
            else:
                raise Exception(colormsg("Error: unexpected units: '%s'"%nominalDacValues[dacName][1],logging.ERROR), os.EX_DATAERR)

    #the nominal reference current is 10 uA and it has a scaling factor of 0.5   
    nominal_iref = 10*0.5

    calInfo = {}
    if args.calFileList != None:
        for line in open(args.calFileList):
            if line[0] == "#":
                continue
            dataEntry = (line.strip()).split()
            shelf   = dataEntry[0]
            slot    = dataEntry[1]
            link    = dataEntry[2]
            calFile = dataEntry[3]
            ohKey = (int(shelf),int(slot),int(link))
            tuple_calInfo = parseCalFile(calFile)
            calInfo[ohKey] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}

    #for each OH, check if calibration files were provided, if not search for the calFile in the $DATA_PATH, if it is not there, then skip that OH for the rest of the script
    for idx,entry in enumerate(crateMap):
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        if ohKey not in calInfo.keys():
            calAdcCalFile = "{0}/{1}/calFile_{2}_{1}.txt".format(dataPath,chamber_config[ohKey],adcName)
            calAdcCalFileExists = os.path.isfile(calAdcCalFile)
            if calAdcCalFileExists:
                tuple_calInfo = parseCalFile(calAdcCalFile)
                calInfo[ohKey] = {'slope' : tuple_calInfo[0], 'intercept' : tuple_calInfo[1]}
            else:    
                print("Skipping Shelf{0}, Slot{1}, OH{2}, detector {3}, missing {4} calibration file:\n\t{5}".format(
                    ohKey[0],
                    ohKey[1],
                    ohKey[2],
                    chamber_config[ohKey],
                    adcName,
                    calAdcCalFile))
                crateMap = np.delete(crateMap,(idx))

    if len(crateMap) == 0:
        raise Exception(colormsg('No OHs with a calFile, exiting.',logging.ERROR),os.EX_DATAERR)
           
    # Initialize nested dictionaries
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_DACvsADC_Graphs = ndict()
    dict_RawADCvsDAC_Graphs = ndict()
    dict_DACvsADC_Funcs = ndict()

    print("Initializing TObjects")

    # Initialize a TGraphErrors and a TF1 for each vfat
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            for vfat in range(0,24):
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat] = r.TGraphErrors()
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetXaxis().SetTitle(dacName)
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetYaxis().SetTitle(adcName)
                dict_DACvsADC_Graphs[dacName][ohKey][vfat] = r.TGraphErrors()
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetTitle("VFAT{}".format(vfat))
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetMarkerSize(5)
                #the reversal of x and y is intended - we want to plot the dacName variable on the y-axis and the adcName variable on the x-axis
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetYaxis().SetTitle(dacName)
                if nominalDacValues[dacName][1][len(nominalDacValues[dacName][1])-1] == 'A':
                    dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetXaxis().SetTitle(adcName + " (#muA)")
                else:
                    dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetXaxis().SetTitle(adcName + " (mV)")
                #we will use a fifth degree polynomial to do the fit
                dict_DACvsADC_Funcs[dacName][ohKey][vfat] = r.TF1("DAC Scan Function","[0]*x^5+[1]*x^4+[2]*x^3+[3]*x^2+[4]*x+[5]")
                dict_DACvsADC_Funcs[dacName][ohKey][vfat].SetLineWidth(1)
                dict_DACvsADC_Funcs[dacName][ohKey][vfat].SetLineStyle(3)

    outputFiles = {}         
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        if scandate == 'noscandate':
            outputFiles[ohKey] = r.TFile(elogPath+"/"+chamber_config[ohKey]+"/"+args.outfilename,'recreate')
        else:    
            outputFiles[ohKey] = r.TFile(dataPath+"/"+chamber_config[ohKey]+"/dacScans/"+scandate+"/"+args.outfilename,'recreate')

    print("Looping over stored events in dacScanTree")

    # Loop over events in the tree and fill plots
    for event in dacScanTree:
        ohKey = (event.shelf,event.slot,event.link)
        vfat = event.vfatN

        if vfat not in dict_nonzeroVFATs[ohKey]:
            continue

        #the output of the calibration is mV
        calibrated_ADC_value=calInfo[ohKey]['slope'][vfat]*event.dacValY+calInfo[ohKey]['intercept'][vfat]
        calibrated_ADC_error=calInfo[ohKey]['slope'][vfat]*event.dacValY_Err

        #Get the DAC Name in question
        dacName = str(event.nameX.data())

        #Use Ohm's law to convert the currents to voltages. The VFAT3 team told us that a 20 kOhm resistor was used.
        if nominalDacValues[dacName][1][len(nominalDacValues[dacName][1])-1] == "A":

            #V (mV) = I (uA) R (kOhm)
            #V (10^-3) = I (10^-6) R (10^3)
            calibrated_ADC_value = calibrated_ADC_value/20.0
            calibrated_ADC_error = calibrated_ADC_error/20.0

            if dacName != 'CFG_IREF':
                calibrated_ADC_value -= nominal_iref 

            calibrated_ADC_value /= nominalDacScalingFactors[dacName]
                
        #the reversal of x and y is intended - we want to plot the dacName variable on the y-axis and the adcName variable on the x-axis
        #the dacName variable is the DAC register that is scanned, and we want to determine its nominal value
        if args.assignXErrors:
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPoint(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPointError(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN()-1,calibrated_ADC_error,event.dacValX_Err)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPoint(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN(),event.dacValX,event.dacValY)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPointError(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN()-1,event.dacValX_Err,0)
        else:
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPoint(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN(),calibrated_ADC_value,event.dacValX)
            dict_DACvsADC_Graphs[dacName][ohKey][vfat].SetPointError(dict_DACvsADC_Graphs[dacName][ohKey][vfat].GetN()-1,calibrated_ADC_error,0)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPoint(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN(),event.dacValX,event.dacValY)
            dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].SetPointError(dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].GetN()-1,0,0)

    print("fitting DAC vs. ADC distributions")

    # Fit the TGraphErrors objects
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            for vfat in range(0,24):
                if vfat not in dict_nonzeroVFATs[ohKey]:
                    #so that the output plots for these VFATs are completely empty
                    dict_DACvsADC_Funcs[dacName][ohKey][vfat].SetLineColor(0)
                    continue
                #the fits fail when the errors on dacValY (the x-axis variable) are used
                dict_DACvsADC_Graphs[dacName][ohKey][vfat].Fit(dict_DACvsADC_Funcs[dacName][ohKey][vfat],"QEX0")

    # Create Determine max DAC size
    dict_maxByDacName = {}
    from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
    for dacSelect,dacInfo in maxVfat3DACSize.iteritems():
        dict_maxByDacName[dacInfo[1]]=dacInfo[0]

    print("Determining nominal values for bias voltage and/or current settings")

    # Determine DAC values to achieve recommended bias voltage and current settings
    graph_dacVals = ndict()
    dict_dacVals = ndict()
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        maxDacValue = dict_maxByDacName[dacName]

        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            graph_dacVals[dacName][ohKey] = r.TGraph()
            graph_dacVals[dacName][ohKey].SetMinimum(0)
            graph_dacVals[dacName][ohKey].GetXaxis().SetTitle("VFATN")
            graph_dacVals[dacName][ohKey].GetYaxis().SetTitle("nominal {} value".format(dacName))

            for vfat in range(0,24):
                if vfat not in dict_nonzeroVFATs[ohKey]:
                    continue

                #evaluate the fitted function at the nominal current or voltage value and convert to an integer
                fittedDacValue = int(dict_DACvsADC_Funcs[dacName][ohKey][vfat].Eval(nominal[dacName]))
                finalDacValue = max(0,min(maxDacValue,fittedDacValue))
                
                if fittedDacValue != finalDacValue:
                    errorMsg = "Warning: when fitting VFAT{5} of chamber {6} (Shelf{7},Slot{8},OH{4}) DAC {0} the fitted value, {1}, is outside range the register can hold: [0,{2}]. It will be replaced by {3}.".format(
                            dacName,
                            fittedDacValue,
                            maxDacValue,
                            finalDacValue,
                            ohKey[2],
                            vfat,
                            chamber_config[ohKey],
                            ohKey[0],
                            ohKey[1])
                    print(colormsg(errorMsg,logging.ERROR))
                    
                dict_dacVals[dacName][ohKey][vfat] = finalDacValue
                graph_dacVals[dacName][ohKey].SetPoint(graph_dacVals[dacName][ohKey].GetN(),vfat,dict_dacVals[dacName][ohKey][vfat])

    print("Writing output data")

    # Write out the dacVal results to a root file, a text file, and the terminal
    outputTxtFiles_dacVals = ndict()
    for idx in range(len(dacNameArray)):
        dacName = np.asscalar(dacNameArray[idx])
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            if scandate == 'noscandate':
                outputTxtFiles_dacVals[dacName][ohKey] = open("{0}/{1}/NominalValues-{2}.txt".format(elogPath,chamber_config[ohKey],dacName),'w')
            else:
                outputTxtFiles_dacVals[dacName][ohKey] = open("{0}/{1}/dacScans/{2}/NominalValues-{3}.txt".format(dataPath,chamber_config[ohKey],scandate,dacName),'w')

    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        # Per VFAT Poosition
        for vfat in range(0,24):
            thisVFATDir = outputFiles[ohKey].mkdir("VFAT{0}".format(vfat))

            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])

                thisDACDir = thisVFATDir.mkdir(dacName)
                thisDACDir.cd()

                dict_DACvsADC_Graphs[dacName][ohKey][vfat].Write("g_VFAT{0}_DACvsADC_{1}".format(vfat,dacName))
                dict_DACvsADC_Funcs[dacName][ohKey][vfat].Write("func_VFAT{0}_DACvsADC_{1}".format(vfat,dacName))
                dict_RawADCvsDAC_Graphs[dacName][ohKey][vfat].Write("g_VFAT{0}_RawADCvsDAC_{1}".format(vfat,dacName))

                if vfat in dict_nonzeroVFATs[ohKey]:
                    outputTxtFiles_dacVals[dacName][ohKey].write("{0}\t{1}\n".format(vfat,dict_dacVals[dacName][ohKey][vfat]))

        # Summary Case
        dirSummary = outputFiles[ohKey].mkdir("Summary")
        dirSummary.cd()
        for idx in range(len(dacNameArray)):
            dacName = np.asscalar(dacNameArray[idx])

            # Store summary graph
            graph_dacVals[dacName][ohKey].Write("g_NominalvsVFATPos_{0}".format(dacName))

            # Store summary grid canvas and print images
            canv_Summary = make3x8Canvas("canv_Summary_{0}".format(dacName),dict_DACvsADC_Graphs[dacName][ohKey],'APE1',dict_DACvsADC_Funcs[dacName][ohKey],'')
            if scandate == 'noscandate':
                canv_Summary.SaveAs("{0}/{1}/Summary_{1}_DACScan_{2}.png".format(elogPath,chamber_config[ohKey],dacName))
            else:
                canv_Summary.SaveAs("{0}/{1}/dacScans/{2}/Summary{1}_DACScan_{2}.png".format(dataPath,chamber_config[ohKey],scandate,dacName))

    # Print Summary?
    if args.printSum:
        print("| shelf | slot | ohN | vfatN | dacName | Value |")
        print("| :---: | :--: | :-: | :---: | :-----: | :---: |")
        for entry in crateMap:
            ohKey = (entry['shelf'],entry['slot'],entry['link'])
            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])
            
                for vfat in range(0,24):
                    if vfat not in dict_nonzeroVFATs[ohKey]:
                        continue

                    print("| {0} | {1} | {2} | {3} | {4} | {5} |".format(
                        ohKey[0],
                        ohKey[1],
                        ohKey[2],
                        vfat,
                        dacName,
                        dict_dacVals[dacName][ohKey][vfat])
                    )
                    pass
                pass
            pass
        pass

    return dict_dacVals

def filePathExists(searchPath, subPath=None, debug=False):
    import os
    
    testPath = searchPath
    if subPath is not None:
        testPath = "%s/%s"%(searchPath, subPath)

    if not os.path.exists(testPath):
        if debug:
            print "Unable to find location: %s"%(testPath)
        return False
    else:
        if debug:
            print "Found %s"%s(testPath)
        return True

def first_index_gt(data_list, value):
    """
    http://code.activestate.com/recipes/578071-fast-indexing-functions-greater-than-less-than-equ/
    
    return the first index greater than value from a given list like object.
    If value is greater than all elements in the list like object, the length 
    of the list like object is returned instead
    """
    try:
        index = next(data[0] for data in enumerate(data_list) if data[1] > value)
        return index
    except StopIteration: 
        return len(data_list)

def formatSciNotation(value, digits=2):
    """
    Returns a string formated in scientific notation with a number of digits to the
    right of the decimal place equal to the digits value
    """
    from decimal import Decimal

    sciNotation = '%.{0}E'.format(digits)

    return sciNotation % Decimal(value)

def get2DMapOfDetector(vfatChanLUT, obsData, mapName, zLabel):
    """
    Generates a 2D map of the detector as a TH2D. Y-axis will be ieta. X-axis will be ROBstr (strip),
    vfat channel or panasonic pin number.  The z-axis will be the elements of obsData with label zLabel

    vfatChanLUT - Nested dictionary specifying the VFAT channel to strip and PanPin mapping;
                  see getMapping() for details on expected format
    obsData     - Numpy array w/3072 entries storing, index goes as [vfat*128+chan]
    mapName     - Type of map to be produced, will be the x-axis.  See mappingNames of anaInfo
                  for possible options
    zLabel      - Label of the z-axis
    """

    from anaInfo import mappingNames
    import os

    if mapName not in mappingNames:
        print("get2DMapOfDetector(): mapName %s not recognized"%mapName)
        print("\tAvailable options are:")
        print("\t",mappingNames)
        raise LookupError

    import ROOT as r
    hRetMap = r.TH2F("ieta_vs_%s_%s"%(mapName,zLabel),"",384,-0.5,383.5,8,0.5,8.5)
    hRetMap.SetXTitle(mapName)
    hRetMap.SetYTitle("i#eta")
    hRetMap.SetZTitle(zLabel)

    from gempython.gemplotting.mapping.chamberInfo import chamber_vfatPos2iEtaiPhi
    for idx in range(3072):
        # Determine vfat, ieta, and iphi
        vfat = idx // 128
        ieta = chamber_vfatPos2iEtaiPhi[vfat][0]
        iphi = chamber_vfatPos2iEtaiPhi[vfat][1]

        # Determine strip, panasonic pin, or channel
        chan = idx % 128
        stripPinOrChan = vfatChanLUT[vfat][mapName][chan]

        # Set Bin Content of Histogram
        hRetMap.SetBinContent( ((iphi-1)*128+stripPinOrChan)+1, ieta, obsData[idx])
        pass

    return hRetMap

def getCyclicColor(idx):
    return 30+4*idx

def getDirByAnaType(anaType, cName, ztrim=4):
    from anaInfo import ana_config
    
    import os

    # Check anaType is understood
    if anaType not in ana_config.keys():
        print "getDirByAnaType() - Invalid analysis specificed, please select only from the list:"
        print ana_config.keys()
        exit(os.EX_USAGE)
        pass

    # Check Paths
    from ...utils.wrappers import envCheck
    envCheck('DATA_PATH')
    dataPath  = os.getenv('DATA_PATH')

    dirPath = ""
    if anaType == "dacScanV3":
        dirPath = "%s/%s"%(dataPath,anaType)
    elif anaType == "latency":
        dirPath = "%s/%s/%s/trk/"%(dataPath,cName,anaType)
    elif anaType == "sbitMonInt":
        dirPath = "%s/%s/sbitMonitor/intTrig/"%(dataPath,cName)
    elif anaType == "sbitMonRO":
        dirPath = "%s/%s/sbitMonitor/readout/"%(dataPath,cName)
    elif anaType == "sbitRatech":
        dirPath = "%s/%s/sbitRate/perchannel/"%(dataPath,cName)
    elif anaType == "sbitRateor":
        dirPath = "%s/%s/sbitRate/channelOR/"%(dataPath,cName)
    elif anaType == "scurve":
        dirPath = "%s/%s/%s/"%(dataPath,cName,anaType)
    elif anaType == "temperature":
        dirPath = "%s/%s"%(dataPath,anaType)
    elif anaType == "thresholdch":
        dirPath = "%s/%s/threshold/channel/"%(dataPath,cName)
    elif anaType == "thresholdvftrig":
        dirPath = "%s/%s/threshold/vfat/trig/"%(dataPath,cName)
    elif anaType == "thresholdvftrk":
        dirPath = "%s/%s/threshold/vfat/trk/"%(dataPath,cName)
    elif anaType == "trim":
        dirPath = "%s/%s/%s/z%f/"%(dataPath,cName,anaType,ztrim)
    elif anaType == "trimV3":
        dirPath = "%s/%s/trim/"%(dataPath,cName)

    return dirPath

def getEmptyPerVFATList(n_vfat=24):
    """
    Returns a list of lists
    Each of the inner lists are empty

    There are n_vfat inner lists
    """

    return [ [] for vfat in range(0,n_vfat) ]

def getMapping(mappingFileName, isVFAT2=True):
    """
    Returns a nested dictionary, the outer dictionary uses VFAT position as the has a key,
    the inner most dict has keys from the list anaInfo.py mappingNames.
    
    The inner dict stores a list whose index is ordered by ASIC channel number, accessing
    the i^th element of this list gives either the readout strip number, the readout connector
    pin number, or the vfat channel number as shown in this example:

        ret_dict[vfatN]['Strip'][asic_chan] is the strip number
        ret_dict[vfatN]['PanPin'][asic_chan] is the pin number on the readout connector
        ret_dict[vfatN]['vfatCH'][asic_chan] is the vfat channel number

    mappingFile - physical filename of file which contains the mapping information, 
                  expected format:

                        vfat/I:strip/I:channel/I:PanPin/I
                        0	0	16	63
                        0	1	20	62
                        0	2	24	61
                        ...
                        ...

                  Here these column headings are:
                        vfat - the VFAT position on the detector (e.g. vfatN)
                        strip - the anode strip on the readout board in an ieta row
                        channel - the channel on the ASIC
                        PanPin - the pin number on the panasonic connector
    """
    from ...utils.nesteddict import nesteddict

    from anaInfo import mappingNames
    import ROOT as r

    # Try to get the mapping data
    try:
        mapFile = open(mappingFileName, 'r')
    except IOError as e:
        print "Exception:", e
        print "Failed to open: '%s'"%mappingFileName
    else:
        listMapData = mapFile.readlines()
    finally:
        mapFile.close()

    # strip trhe end of line character
    listMapData = [x.strip('\n') for x in listMapData]

    # setup the look up table
    ret_mapDict = nesteddict()
    for vfat in range(0,24):
        for name in mappingNames:
            ret_mapDict[vfat][name] = [0] * 128

    # Set the data in the loop up table
    for idx, line in enumerate(listMapData):
        if idx == 0: 
            continue # skip the header line
        mapping = line.rsplit('\t')
        if isVFAT2: 
            ret_mapDict[int(mapping[0])]['Strip'][int(mapping[2]) - 1] = int(mapping[1])
            ret_mapDict[int(mapping[0])]['PanPin'][int(mapping[2]) -1] = int(mapping[3])
            ret_mapDict[int(mapping[0])]['vfatCH'][int(mapping[2]) - 1] = int(mapping[2]) - 1
        else: #EDMS document numbers VFAT3 channels from [0,127]
            ret_mapDict[int(mapping[0])]['Strip'][int(mapping[2])] = int(mapping[1])
            ret_mapDict[int(mapping[0])]['PanPin'][int(mapping[2])] = int(mapping[3])
            ret_mapDict[int(mapping[0])]['vfatCH'][int(mapping[2])] = int(mapping[2])

    return ret_mapDict

def getStringNoSpecials(inputStr):
    """
    returns a string without special characters
    """

    inputStr = inputStr.replace('*','')
    inputStr = inputStr.replace('-','')
    inputStr = inputStr.replace('+','')
    inputStr = inputStr.replace('(','')
    inputStr = inputStr.replace(')','')
    inputStr = inputStr.replace('/','')
    inputStr = inputStr.replace('{','')
    inputStr = inputStr.replace('}','')
    inputStr = inputStr.replace('#','')

    return inputStr

def initVFATArray(array_dtype, nstrips=128):
    import numpy as np
    
    list_dtypeTuple = []

    for idx in range(0,len(array_dtype)):
        if array_dtype.names[idx] == 'vfatN':   continue
        if array_dtype.names[idx] == 'vfatCh':  continue
        if array_dtype.names[idx] == 'panPin':  continue
        if array_dtype.names[idx] == 'ROBstr':  continue
        list_dtypeTuple.append((array_dtype.names[idx],array_dtype[idx]))
        pass

    return np.zeros(nstrips, dtype=list_dtypeTuple)

#Use inter-quartile range (IQR) to reject outliers
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierIQR(arrayData):
    import numpy as np
    
    dMin    = np.min(arrayData,     axis=0)
    dMax    = np.max(arrayData,     axis=0)
    median  = np.median(arrayData,  axis=0)

    q1,q3   = np.percentile(arrayData, [25,75], axis=0)
    IQR     = q3 - q1

    return (arrayData < (q1 - 1.5 * IQR)) | (arrayData > (q3 + 1.5 * IQR))

#Use inter-quartile range (IQR) to reject outliers, but consider only high or low tail
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierIQROneSided(arrayData, rejectHighTail=True):
    import numpy as np
    
    dMin    = np.min(arrayData,     axis=0)
    dMax    = np.max(arrayData,     axis=0)
    median  = np.median(arrayData,  axis=0)

    q1,q3   = np.percentile(arrayData, [25,75], axis=0)
    IQR     = q3 - q1

    if rejectHighTail:
        return arrayData > (q3 + 1.5 * IQR)
    else:
        return arrayData < (q1 - 1.5 * IQR)

#Use Median absolute deviation (MAD) to reject outliers
#See: https://github.com/joferkington/oost_paper_code/blob/master/utilities.py
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierMAD(arrayData, thresh=3.5):
    import numpy as np
    
    median = np.median(arrayData, axis=0)
    diff = np.abs(arrayData - median)
    med_abs_deviation = np.median(diff)

    if med_abs_deviation == 0:
        return isOutlierIQR(arrayData)
    else:
        modified_z_score = 0.6745 * diff / med_abs_deviation
        return modified_z_score > thresh

#Use MAD to reject outliers, but consider only high or low tail
#Returns a boolean array with True if points are outliers and False otherwise.
def isOutlierMADOneSided(arrayData, thresh=3.5, rejectHighTail=True):
    import numpy as np
    
    median = np.median(arrayData, axis=0)
    diff = arrayData - median
    med_abs_deviation = np.median(np.abs(diff))

    if med_abs_deviation == 0:
        return isOutlierIQROneSided(arrayData, rejectHighTail)
    else:
        modified_z_score = 0.6745 * diff / med_abs_deviation

        if rejectHighTail:
            return modified_z_score > thresh
        else:
            return modified_z_score < -1.0 * thresh

def make2x4Canvas(name, initialContent = None, initialDrawOpt = '', secondaryContent = None, secondaryDrawOpt = '', canv=None):
    """
    Creates a 2x4 canvas for summary plots.

    name - TName of output TCanvas
    initialContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on the canvas.
    initialDrawOpt - draw option to be used when drawing elements of initialContent
    secondaryContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on top of the canvas.
    secondaryDrawOpt - draw option to be used when drawing elements of secondaryContent
    canv - TCanvas previously produced by make3x8Canvas() or one that has been subdivided into a 3x8 grid
    """

    import ROOT as r
    
    if canv is None:
        canv = r.TCanvas(name,name,500*8,500*3)
        canv.Divide(4,2)

    if initialContent is not None:
        for ieta in range(1,9):
            canv.cd(ieta)
            initialContent[ieta].Draw(initialDrawOpt)
    if secondaryContent is not None:
        for ieta in range(1,9):
            canv.cd(ieta)
            secondaryContent[ieta].Draw("same%s"%secondaryDrawOpt)
    canv.Update()
    return canv

def make3x8Canvas(name, initialContent = None, initialDrawOpt = '', secondaryContent = None, secondaryDrawOpt = '', canv=None):
    """
    Creates a 3x8 canvas for summary plots.

    name - TName of output TCanvas
    initialContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on the canvas.
    initialDrawOpt - draw option to be used when drawing elements of initialContent
    secondaryContent - either None or an array of 24 (one per VFAT) TObjects that will be drawn on top of the canvas.
    secondaryDrawOpt - draw option to be used when drawing elements of secondaryContent
    canv - TCanvas previously produced by make3x8Canvas() or one that has been subdivided into a 3x8 grid
    """

    import ROOT as r
    from ..mapping.chamberInfo import chamber_vfatPos2PadIdx
    
    if canv is None:
        canv = r.TCanvas(name,name,500*8,500*3)
        canv.Divide(8,3)

    if initialContent is not None:
        for vfat in range(24):
            canv.cd(chamber_vfatPos2PadIdx[vfat])
            initialContent[vfat].Draw(initialDrawOpt)
    if secondaryContent is not None:
        for vfat in range(24):
            canv.cd(chamber_vfatPos2PadIdx[vfat])
            secondaryContent[vfat].Draw("same%s"%secondaryDrawOpt)
    canv.Update()
    return canv

def makeListOfScanDatesFile(chamberName, anaType, startDate=None, endDate=None, delim='\t', ztrim=4):
    """
    Given a starting scandate startDate and an ending scandate endDate this
    will make a text file for chamberName which is a two-column list of 
    scandates for anaType compatible with parseListOfScanDatesFile()

    chamberName - Chamber name, expected to be in chamber_config.values()
    startDate   - starting scandate in YYYY.MM.DD.hh.mm format, if None then
                  the earliest possible date is used
    endDate     - ending scandate in YYYY.MM.DD.hh.mm format, if None then
                  today is used (latest possible date)
    delim       - delimiter to use in output file name
    """

    from ...utils.wrappers import envCheck, runCommand
    envCheck('DATA_PATH')

    import datetime
    startDay = datetime.date(datetime.MINYEAR,1,1)
    if startDate is not None:
        startDateInfo = [ int(info) for info in startDate.split(".") ]
        startDay = datetime.date(startDateInfo[0], startDateInfo[1], startDateInfo[2])
        pass

    endDay = datetime.date.today()
    if endDate is not None:
        endDateInfo = [ int(info) for info in endDate.split(".") ]
        endDay = datetime.date(endDateInfo[0], endDateInfo[1], endDateInfo[2])
        pass

    import os
    dirPath = getDirByAnaType(anaType, chamberName, ztrim)
    listOfScanDates = os.listdir(dirPath)

    try:
        listOfScanDatesFile = open('%s/listOfScanDates.txt'%dirPath,'w+')
    except IOError as e:
        print "Exception:", e
        print "Failed to open write output file"
        print "Is the below directory writeable?"
        print ""
        print "\t%s"%dirPath
        print ""
        exit(os.EX_IOERR)
        pass
    
    listOfScanDatesFile.write('ChamberName%sscandate\n'%delim)
    for scandate in listOfScanDates:
	if "current" == scandate:
	    continue
        try:
            scandateInfo = [ int(info) for info in scandate.split('.') ]
        except ValueError as e:
            print "Skipping directory %s/%s"%(dirPath,scandate)
            continue
        thisDay = datetime.date(scandateInfo[0],scandateInfo[1],scandateInfo[2])

        if (startDay < thisDay and thisDay <= endDay):
            listOfScanDatesFile.write('%s%s%s\n'%(chamberName,delim,scandate))
            pass
        pass

    listOfScanDatesFile.close()
    runCommand( ['chmod','g+rw','%s/listOfScanDates.txt'%dirPath] )

    return

def parseCalFile(filename=None):
    """
    Gives the conversion between VCal/CFG_CAL_DAC to fC from either
    an optional external file (filename) or the hard coded vfat2 
    values.

    Returns a tuple of numpy arrays where index 0 (1) of the tuple
    corresponds to the slope (intercept) arrays.  The returned 
    arrays are indexed by VFAT position.
    
    The conversion follows via:

    fC = ret_tuple[0][vfat] * CAL_DAC + ret_tuple[1][vfat]

    The structure of filename, if supplied, is expected to be:

        vfatN/I:slope/F:intercept/F
        0   0.2692  -2.629748
        1   0.238106    -2.65316
        2   0.2532  -2.193826
        3   0.276783    -2.477547
        ...
        5   1.000000    0.000000    
        ...
        ...

    Inputing a slope (intercept) of 1.0 (0.0) will keep the numbers
    in DAC units
    """

    import numpy as np
    import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
    import ROOT as r

    # Set the CAL DAC to fC conversion
    calDAC2Q_b = np.zeros(24)
    calDAC2Q_m = np.zeros(24)
    if filename is not None:
        list_bNames = ["vfatN","slope","intercept"]
        calTree = r.TTree('calTree','Tree holding VFAT Calibration Info')
        calTree.ReadFile(filename)
        array_CalData = rp.tree2array(tree=calTree, branches=list_bNames)
    
        for dataPt in array_CalData:
            calDAC2Q_b[dataPt['vfatN']] = dataPt['intercept']
            calDAC2Q_m[dataPt['vfatN']] = dataPt['slope']
            pass
    else:
        calDAC2Q_b = -0.8 * np.ones(24)
        calDAC2Q_m = 0.05 * np.ones(24)
        pass

    return (calDAC2Q_m, calDAC2Q_b)

def parseListOfScanDatesFile(filename, alphaLabels=False, delim='\t'):
    """
    Parses a filename which describes a list of scandates.  Two formats of the filename
    are supported, one in which there are three columns and one in which there are two.
    The first column is always expected to be the chamber name, the second column is 
    always expected to be the scandate.  If a third column is present it is expected to
    be an independent variable and will be alphanumeric input.  Two examples are presented:

    Example1, two columns:

    ChamberName scandate
    GE11-VI-L-CERN-0001    2017.08.11.16.30
    GE11-VI-L-CERN-0001    2017.08.14.20.54
    GE11-VI-L-CERN-0001    2017.08.30.15.03

    Example2, three columns:

    ChamberName scandate indepVarName
    GE11-VI-L-CERN-0001    2017.08.11.16.30 100
    GE11-VI-L-CERN-0001    2017.08.14.20.54 200
    GE11-VI-L-CERN-0001    2017.08.30.15.03 300

    Please note that '#' character is understood as a comment and lines starting with 
    this character will be skipped.

    Arguments are described as:
    
    filename - physical filename of input list of scandate files
    alphaLabels - True (False): the optional third column is understood as alphanumeric (floating point)

    The return value is a tuple:
        [0] -> updated parsedListOfScanDates
        [1] -> indepVarName if present (empty string if not)
    """

    import os

    # Check input file
    try:
        fileScanDates = open(filename, 'r') 
    except IOError as e:
        print '%s does not seem to exist or is not readable'%(filename)
        print e
        exit(os.EX_NOINPUT)
        pass

    parsedListOfScanDates = []
    strIndepVar = ""
    indepVar = ""
    for i,line in enumerate(fileScanDates):
        if line[0] == "#":
            continue

        # Split the line
        line = line.strip('\n')
        analysisList = line.rsplit(delim) #chamber name, scandate, independent var

        # Get the indepVar name if it is present, 
        # Always skip the first line
        if i==0:
            if len(analysisList) == 3:
                strIndepVar = analysisList[2]
            elif len(analysisList) == 2:
                strIndepVar = analysisList[1]
            continue

        cName = analysisList[0]
        scandate = analysisList[1]
        if len(analysisList) == 2:
            indepVar = scandate
        elif len(analysisList) == 3:
            if alphaLabels:
                indepVar = analysisList[2]
            else:
                try:
                    indepVar = float(analysisList[2])
                except Exception as e:
                    print("Non-numeric input given, maybe you ment to call with option 'alphaLabels=True'?")
                    print("Exiting")
                    exit(os.EX_USAGE)
        else:
            print "Input format incorrect"
            print "I was expecting a delimited file using '%s' with all lines having either 2 or 3 entries"%delim
            print "But I received:"
            print "\t%s"%(line)
            print "Exiting"
            exit(os.EX_USAGE)
            pass
        
        parsedListOfScanDates.append( (cName, scandate, indepVar) )

    return (parsedListOfScanDates,strIndepVar)

#Use Median absolute deviation (MAD) to reject outliers
#See: http://stackoverflow.com/questions/22354094/pythonic-way-of-detecting-outliers-in-one-dimensional-observation-data
#And also: http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
def rejectOutliersMAD(arrayData, thresh=3.5):    
    arrayOutliers = isOutlierMAD(arrayData, thresh)
    return arrayData[arrayOutliers != True]

#Use MAD to reject outliers, but consider only high or low tail
def rejectOutliersMADOneSided(arrayData, thresh=3.5, rejectHighTail=True):
    arrayOutliers = isOutlierMADOneSided(arrayData, thresh, rejectHighTail)
    return arrayData[arrayOutliers != True]

def saveSummary(dictSummary, dictSummaryPanPin2=None, name='Summary', trimPt=None, drawOpt="colz"):
    """
    Makes an image with summary canvases drawn on it

    dictSummary        - dict of TObjects to be drawn, one per VFAT.  Each will be 
                         drawn on a separate pad
    dictSummaryPanPin2 - Optional, as dictSummary but if the independent variable is the
                         readout connector pin this is the other side of the connector
    name               - Name of output image
    trimPt             - Optional, list of trim points the dependent variable was aligned
                         to if it is the result of trimming.  One entry per VFAT
    drawOpt            - Draw option
    """

    import ROOT as r
    from ..mapping.chamberInfo import chamber_vfatPos2PadIdx

    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    if dictSummaryPanPin2 is None:
        canv = make3x8Canvas('canv', dictSummary, drawOpt)
        for vfat in range(0,24):
            canv.cd(chamber_vfatPos2PadIdx[vfat])
            if trimPt is not None and trimLine is not None:
                trimLine = r.TLine(-0.5, trimVcal[vfat], 127.5, trimVcal[vfat])
                legend.Clear()
                legend.AddEntry(trimLine, 'trimVCal is %f'%(trimVcal[vfat]))
                legend.Draw('SAME')
                trimLine.SetLineColor(1)
                trimLine.SetLineWidth(3)
                trimLine.Draw('SAME')
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
                dictSummary[ieta+(8*iphi)].Draw(drawOpt)
                canv.Update()
                canv.cd((ieta+9 + iphi*16)%48 + 16)
                dictSummaryPanPin2[ieta+(8*iphi)].Draw(drawOpt)
                canv.Update()
                pass
            pass
        pass

    canv.SaveAs(name)

    return

def saveSummaryByiEta(dictSummary, name='Summary', trimPt=None, drawOpt="colz"):
    """
    Makes an image with summary canvases drawn on it

    dictSummary        - dict of TObjects to be drawn, one per ieta.  Each will be 
                         drawn on a separate pad
    name               - Name of output image
    trimPt             - Optional, list of trim points the dependent variable was aligned
                         to if it is the result of trimming.  One entry per VFAT
    drawOpt            - Draw option
    """

    import ROOT as r

    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    canv = make2x4Canvas(name='canv', initialContent=dictSummary, initialDrawOpt=drawOpt)
    for ieta in range(0,8):
        canv.cd(ieta+1)
        if trimPt is not None and trimLine is not None:
            trimLine = r.TLine(-0.5, trimVcal[ieta], 127.5, trimVcal[ieta])
            legend.Clear()
            legend.AddEntry(trimLine, 'trimVCal is %f'%(trimVcal[vfat]))
            legend.Draw('SAME')
            trimLine.SetLineColor(1)
            trimLine.SetLineWidth(3)
            trimLine.Draw('SAME')
            pass
        canv.Update()
        pass

    canv.SaveAs(name)

    return

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

    # Check $ENV
    from gempython.utils.wrappers import envCheck
    envCheck("DATA_PATH")
    envCheck("ELOG_PATH")

    import os
    dataPath = os.getenv("DATA_PATH")
    elogPath = os.getenv("ELOG_PATH") 

    # Set default histogram behavior
    import ROOT as r
    r.TH1.SetDefaultSumw2(False)
    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(1111111)

    print("Loading info from input TTree")

    # Get the data
    import root_numpy as rp
    import numpy as np
    list_bNames = ['dacValX','link','nameX','rate','shelf','slot','vfatCH','vfatN']

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
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        if scandate == 'noscandate':
            runCommand(["mkdir", "-p", "{0}/{1}".format(elogPath,chamber_config[ohKey])])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(elogPath,chamber_config[ohKey])])
        else:
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", chamber_config[ohKey])
            else:
                strDirName = getDirByAnaType("sbitRateor", chamber_config[ohKey])
                pass
            runCommand(["mkdir", "-p", "{0}/{1}".format(strDirName,scandate)])
            runCommand(["chmod", "g+rw", "{0}/{1}".format(strDirName,scandate)])
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
            for vfat in range(0,25): #24th VFAT represents "overall case"
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
        if scandate == 'noscandate':
            outputFiles[ohKey] = r.TFile(elogPath+"/"+chamber_config[ohKey]+"/"+outfilename,'recreate')
        else:    
            if perchannel:
                strDirName = getDirByAnaType("sbitRatech", chamber_config[ohKey])
            else:
                strDirName = getDirByAnaType("sbitRateor", chamber_config[ohKey])
                pass
            outputFiles[ohKey] = r.TFile(strDirName+scandate+"/"+outfilename,'recreate')
            pass
        pass

    # Loop over events the tree and fill plots
    print("Looping over stored events in rateTree")
    from math import sqrt 
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
            print("Point Number: ", counter)
            print("event.vfatCH = ", event.vfatCH)
            print("dacName = ", dacName)
            print("ohKey = ", ohKey)
            print("vfat = ", vfat)
            print("dict_Rate1DVsDACNameX[dacName].keys() = ", dict_Rate1DVsDACNameX.keys() )
            print("dict_Rate1DVsDACNameX[dacName][ohKey].keys() = ", dict_Rate1DVsDACNameX[dacName][ohKey].keys() )
            print("dict_Rate1DVsDACNameX[dacName][ohKey][vfat] = ", dict_Rate1DVsDACNameX[dacName][ohKey][vfat] )
            print("dict_Rate1DVsDACNameX = ", dict_Rate1DVsDACNameX)
            exit()

            pass
        pass

    print("Determine when SBIT rate falls below {0} Hz and writing output data".format(cutOffRate))
    #from array import array
    dict_dacValsBelowCutOff = ndict()
    for entry in crateMap:
        ohKey = (entry['shelf'],entry['slot'],entry['link'])
        # Per VFAT Poosition
        for vfat in range(0,24):
            thisVFATDir = outputFiles[ohKey].mkdir("VFAT{0}".format(vfat))

            for idx in range(len(dacNameArray)):
                dacName = np.asscalar(dacNameArray[idx])

                thisDACDir = thisVFATDir.mkdir(dacName)
                thisDACDir.cd()

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
        for idx in range(len(dacNameArray)):
            dacName = np.asscalar(dacNameArray[idx])
            if perchannel:
                canv_Summary2D = make3x8Canvas("canv_Summary_Rate2D_vs_{0}".format(dacName),dict_vfatCHVsDACNameX_Rate2D[dacName][ohKey],"TRI1")
                for vfat in range(1,25):
                    canv_Summary2D.cd(vfat).SetLogz()
            else:
                canv_Summary1D = make3x8Canvas("canv_Summary_Rate1D_vs_{0}".format(dacName),dict_Rate1DVsDACNameX[dacName][ohKey],"APE1")
                for vfat in range(1,25):
                    canv_Summary1D.cd(vfat).SetLogy()

            if scandate == 'noscandate':
                if perchannel:
                    canv_Summary2D.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,chamber_config[ohKey],canv_Summary2D.GetName()))
                else:
                    canv_Summary1D.SaveAs("{0}/{1}/{2}_{1}.png".format(elogPath,chamber_config[ohKey],canv_Summary1D.GetName()))
            else:
                if perchannel:
                    strDirName = getDirByAnaType("sbitRatech", chamber_config[ohKey])
                    canv_Summary2D.SaveAs("{0}/{1}/{2}.png".format(strDirName,scandate,canv_Summary2D.GetName()))
                else:
                    strDirName = getDirByAnaType("sbitRateor", chamber_config[ohKey])
                    canv_Summary1D.SaveAs("{0}/{1}/{2}.png".format(strDirName,scandate,canv_Summary1D.GetName()))
                    pass
                pass
            pass
        outputFiles[ohKey].Close()
        pass

    return (perchannel, dict_dacValsBelowCutOff)
